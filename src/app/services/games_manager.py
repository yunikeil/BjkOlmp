import asyncio
from typing import Literal, Any
from dataclasses import dataclass
from json.decoder import JSONDecodeError

from pydantic import ValidationError
from fastapi import Depends, Header, WebSocket, WebSocketException, status

from core.bj_game import bj_core
from core.redis import get_redis_client, get_redis_pipeline


import random

vowels = ['a', 'e', 'i', 'o', 'u']
consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']


def generate_name():
    length = random.randint(3, 10)
    if length <= 0:
        return False

    name = ''
    for i in range(length):
        if i == 0:
            name += random.choice(vowels + consonants)
        
        else:
            if name[-1] in vowels:
                name += random.choice(consonants)
            
            else:
                name += random.choice(vowels)

    return name.capitalize()


@dataclass(frozen=True)
class ConnectionContext:
    """
    """
    websocket: WebSocket
    player: bj_core.RoundPlayer
    websocket_conn_type: Literal["json", "text"]

    def unpack(self):
        return self.player, self.websocket


@dataclass
class WsEventData:
    event_type: str
    data: dict

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "data": self.data,
        }
    
@dataclass
class WSEvent(WsEventData):
    websocket: WebSocket
    
    def get_event_dataclass(self) -> WsEventData:
        return WsEventData(self.event_type, self.data)


class TransactionalEventSystem:
    def __init__(self) -> None:
        self.to_send: dict[WebSocket, list[dict]] = {}
        self.draw_events: dict[WebSocket, dict] = {}

    def add_events(self, *new_events: WSEvent) -> None:
        for event in new_events:
            event_data = event.get_event_dataclass()
            event_dict = event_data.to_dict()
            
            if event.websocket in self.to_send:
                self.to_send[event.websocket].append(event_dict)
                
            else:
                self.to_send[event.websocket] = [event_dict]
    
    def add_draw_event(self, websocket: WebSocket, draw_event: dict):
        self.draw_events[websocket] = draw_event
    
    async def send_events(self, dict_sender: Any = None) -> None:
        for ws, dict_data_list in self.to_send.items():
            if dict_sender:
                await dict_sender(ws, dict_data_list)
            
            else:
                print(f"sended:\n{dict_data_list}")
                print()
                await ws.send_json(
                    {
                        "events": dict_data_list,
                        "draw_event": self.draw_events.get(ws, None),
                    }
                )
            

# TODO если сразу выпадает 21 у игрока логика не опрабатывает запрет некст шагов
class GameConnectionManager:
    ws_connections: dict[str, WebSocket] = {}
    rooms: dict[bj_core.GameRoom, set[str]] = {}
    rooms_players: set[str] = {}

    def __init__(self):
        pass
        
    async def __call__(
        self,
        websocket: WebSocket,
        publick_name = Header(None, alias="Publick-Name"),
        ws_type = Header("text", alias="Connection-Type"),
    ):
        if not publick_name:
            publick_name = generate_name()
        
        player = bj_core.RoundPlayer(publick_name)
        return ConnectionContext(websocket, player, ws_type), self

    async def __raise(
        self, conn_context: ConnectionContext, code: int, reason: str | None = None
    ):
        await self.disconnect(conn_context)
        raise WebSocketException(code, reason)

    async def send_event(
        self, event_type: str, data: dict, websocket: WebSocket, draw_event: str = None
    ):
        await websocket.send_json(
            {
                "events": [
                    {
                        "event_type": event_type,
                        "data": data,
                    }
                ],
                "draw_event": draw_event,
            }
        )

    async def broadcast(self, clients_ids: list[int], event_type: str, data: dict, need_draw: bool = None):
        for client_id in clients_ids:
            await self.send_event(event_type, data, self.ws_connections[client_id], need_draw)
           
    async def connect(self, conn_context: ConnectionContext):
        await conn_context.websocket.accept()
        self.ws_connections[conn_context.player.id] = conn_context.websocket
        await self.send_event("base_game_data_update", {"player_id": conn_context.player.id, "my_name": conn_context.player.publick_name}, conn_context.websocket)
    
    async def disconnect(self, conn_context: ConnectionContext):
        del self.ws_connections[conn_context.player.id]
        
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            players.remove(conn_context.player.id)
            room.remove_player(conn_context.player)        
            if len(players) == 0:
                del self.rooms[room]
                return
            
            else:
                await self.broadcast(players, "users_update", {"disconnected": conn_context.player.publick_name})

            break
    
    async def __find_opened_room(self, player: bj_core.RoundPlayer) -> str | None:
        """
        Ищет и автоматически добавляет игрока в существующую игру
        """
        for room, players in self.rooms.items():
            if not room.is_need_player():
                continue
            
            ws_events = []
            event_manager = TransactionalEventSystem()
            full_room_event = WSEvent(
                event_type="game_data_update",
                data=room.to_dict(),
                websocket=self.ws_connections[player.id],
            )
            ws_events.append(full_room_event)
            event_manager.add_draw_event(self.ws_connections[player.id], f"Вы вступили в комнату: {room.id}")
            
            for player_id in players:
                new_user_connected_event = WSEvent(
                    event_type="users_update",
                    data={"connected": player.publick_name},
                    websocket=self.ws_connections[player_id]
                )
                ws_events.append(new_user_connected_event)
                event_manager.add_draw_event(self.ws_connections[player_id], f"В комнату вступил новый игрок: {player.publick_name}")
            
            room.add_player(player)
            self.rooms[room].add(player.id)
            
            event_manager.add_events(*ws_events)
            await event_manager.send_events()
            
            return room.id
    
    async def __create_room(self, player: bj_core.RoundPlayer, max_players: int = 1):
        """
        Создаёт новую игру
        """
        new_room = bj_core.GameRoom(max_players)
        new_room.add_player(player)
        self.rooms[new_room] = {player.id}
        
        await self.send_event("base_game_data_update", {"room_id": new_room.id}, self.ws_connections[player.id])

    async def __process_find_game(self, data: dict, conn_context: ConnectionContext):
        game_type: Literal["new", "old"] = data.get("game_type")
        if game_type == "new":
            max_players = data.get("max_players")
            await self.__create_room(conn_context.player, max_players)
            
        elif game_type == "old":
            room_id = await self.__find_opened_room(conn_context.player)
            if not room_id:
                max_players = data.get("max_players", 2)
                await self.__create_room(conn_context.player, max_players)
            
    async def __process_start_game(self, data: dict, conn_context: ConnectionContext):       
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            room.start_game()
            await self.broadcast(players, "base_game_data_update", {"is_started": True, "accepted_methods": ["do_deal"]})
            break

    async def finish_round(self, room: bj_core.GameRoom, players_ids: list[str], conn_context: ConnectionContext) -> TransactionalEventSystem:
        # Обновление информации пользователей (итоговая)
        ws_events = []
        event_manager = TransactionalEventSystem()
        for player_id in players_ids:
            ws = self.ws_connections[player_id]
            event_manager.add_draw_event(ws, "Игра окончена! Показ результатов")
            full_room_event = WSEvent(
                event_type="finish_game_data_update",
                data=room.to_dict(),
                websocket=ws,
            )
            ws_events.append(full_room_event)
            round_finished_update_event = WSEvent(
                event_type="base_game_data_update",
                data={"is_round_finished": room.is_round_finished},
                websocket=ws,
            )
            ws_events.append(round_finished_update_event)
            # нет информации о том кто сколько и почему проебал

        event_manager.add_events(*ws_events)
        
        return event_manager
    
    async def __process_do_deal(self, data: dict, conn_context: ConnectionContext):
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            # TODO добавить метод для проверки результатов (ожидания игроков с тем, что произошло)
            # Ну или в конце отрисовывать полное поле с доп инфой о след раунде
            bet = int(data.get("bet"))
            is_player_finished = room.do_deal(conn_context.player, bet)
            dealer = room.if_all_with_cards_add_cards_to_dealer()
            event_manager = TransactionalEventSystem()
            ws_events = []
            finish_manager = None
            
            if is_player_finished:
                accepted_methods = []
            else:
                accepted_methods = ["do_stand", "do_double", "do_hit"]
                
            user_next_methods_event = WSEvent(
                event_type="base_game_data_update",
                data={"accepted_methods": accepted_methods},
                websocket=conn_context.websocket
            )
            ws_events.append(user_next_methods_event)
            
            for player_id in players:
                ws = self.ws_connections[player_id]
                event_manager.add_draw_event(
                    ws, f"{conn_context.player.publick_name} сделал ставку!"
                )

                user_create_deal_event = WSEvent(
                    event_type="users_update",
                    data={"user_data": conn_context.player.to_dict()},
                    websocket=ws,
                )
                ws_events.append(user_create_deal_event)
                
                if dealer:
                    dealer_update_event = WSEvent(
                        event_type="dealer_update",
                        data={"dealer_data": dealer.to_dict()},
                        websocket=ws,
                    )
                    ws_events.append(dealer_update_event)
                    if room.check_is_all_players_standed():
                        finish_manager = await self.finish_round(room, players, conn_context)
            
            event_manager.add_events(*ws_events)
            await event_manager.send_events()
            
            if finish_manager:
               await finish_manager.send_events()
        
    async def __process_do_stand(self, data: dict, conn_context: ConnectionContext):
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            room.do_stand(conn_context.player)
            dealer = room.check_is_all_players_standed()
            event_manager = TransactionalEventSystem()
            ws_events = []
            finish_manager = None

            accepted_methods_update = WSEvent(
                event_type="base_game_data_update",
                data={"accepted_methods": []},
                websocket=conn_context.websocket,
            )
            ws_events.append(accepted_methods_update)
            
            for player_id in players:
                ws = self.ws_connections[player_id]
                event_manager.add_draw_event(
                    websocket=ws, draw_event=f"{conn_context.player.publick_name} завершил ход!"
                )

                player_standed_event = WSEvent(
                    event_type="users_update",
                    data={"user_data": conn_context.player.to_dict()},
                    websocket=ws,
                )
                ws_events.append(player_standed_event)
                            
                if dealer:
                    dealer_update_event = WSEvent(
                        event_type="dealer_update",
                        data={"dealer_data": dealer.to_dict()},
                        websocket=ws,
                    )
                    ws_events.append(dealer_update_event)
                    finish_manager = await self.finish_round(room, players, conn_context)

            event_manager.add_events(*ws_events)
            await event_manager.send_events()
            
            if finish_manager:
               await finish_manager.send_events()

    async def __process_do_double(self, data: dict, conn_context: ConnectionContext):
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            is_move_over = room.do_double(conn_context.player)
            dealer = room.check_is_all_players_standed()
            event_manager = TransactionalEventSystem()
            ws_events = []
            finish_manager = None

            if is_move_over:
                accepted_methods = []
            else:
                accepted_methods =  ["do_stand", "do_hit"]
            
            accepted_methods_update = WSEvent(
                event_type="base_game_data_update",
                data={"accepted_methods": accepted_methods},
                websocket=conn_context.websocket,
            )
            ws_events.append(accepted_methods_update)

            
            for player_id in players:
                ws = self.ws_connections[player_id]
                event_manager.add_draw_event(
                    websocket=ws, draw_event=f"{conn_context.player.publick_name} удвоил ставку!"
                )

                user_update_event = WSEvent(
                    event_type="users_update",
                    data={"user_data": conn_context.player.to_dict()},
                    websocket=ws,
                )
                ws_events.append(user_update_event)
                        
                if dealer:
                    dealer_update_event = WSEvent(
                        event_type="dealer_update",
                        data={"dealer_data": dealer.to_dict()},
                        websocket=ws,
                    )
                    ws_events.append(dealer_update_event)
                    finish_manager = await self.finish_round(room, players, conn_context)

            event_manager.add_events(*ws_events)
            await event_manager.send_events()
            
            if finish_manager:
               await finish_manager.send_events()


    async def __process_do_hit(self, data: dict, conn_context: ConnectionContext):
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            is_move_over = room.do_hit(conn_context.player)
            dealer = room.check_is_all_players_standed()
            event_manager = TransactionalEventSystem()
            ws_events = []
            finish_manager = None

            if is_move_over:
                accepted_methods_update = WSEvent(
                    event_type="base_game_data_update",
                    data={"accepted_methods": []},
                    websocket=conn_context.websocket,
                )
                ws_events.append(accepted_methods_update)
            
            for player_id in players:
                ws = self.ws_connections[player_id]
                event_manager.add_draw_event(
                    websocket=ws, draw_event=f"{conn_context.player.publick_name} взял карту!"
                )

                user_update_event = WSEvent(
                    event_type="users_update",
                    data={"user_data": conn_context.player.to_dict()},
                    websocket=ws,
                )
                ws_events.append(user_update_event)


                if dealer:
                    dealer_update_event = WSEvent(
                        event_type="dealer_update",
                        data={"dealer_data": dealer.to_dict()},
                        websocket=ws,
                    )
                    ws_events.append(dealer_update_event)
                    finish_manager = await self.finish_round(room, players, conn_context)

            event_manager.add_events(*ws_events)
            await event_manager.send_events()
            
            if finish_manager:
               await finish_manager.send_events()
        
    async def __process_event_type(
        self,
        event: Literal[
            "find_game",
            "start_game",
            "do_deal",
            "do_stand",
            "do_double",
            "do_hit",
        ],
        data: dict,
        conn_context: ConnectionContext
    ):
        match event:
            case "find_game":
                await self.__process_find_game(data, conn_context)
            case "start_game":
                await self.__process_start_game(data, conn_context)
            case "do_deal":
                await self.__process_do_deal(data, conn_context)
            case "do_stand":
                await self.__process_do_stand(data, conn_context)
            case "do_double":
                await self.__process_do_double(data, conn_context)
            case "do_hit":
                await self.__process_do_hit(data, conn_context)
            
    async def listen_event(
        self, conn_context: ConnectionContext
    ):
        player, websocket = conn_context.unpack()
        client_data: dict = await websocket.receive_json()
        event_type: str = client_data.get("event")
        data: dict = client_data.get("data")
        
        await self.__process_event_type(event_type, data, conn_context)
        
