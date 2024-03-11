import asyncio
from typing import Literal
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

    async def send_event(self, event_type: str, data: dict, websocket: WebSocket):
        await websocket.send_json(
            {
                "event": event_type,
                "data": data,
            }
        )
           
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
            
            room_json = room.to_dict()
            await self.send_event("game_data_update", room_json, self.ws_connections[player.id])
            await self.broadcast(players, "users_update", {"connected": player.publick_name})
            room.add_player(player)
            self.rooms[room].add(player.id)
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
    
    async def __process_do_deal(self, data: dict, conn_context: ConnectionContext):
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            bet = int(data.get("bet"))
            room.do_deal(conn_context.player, bet)
            await self.send_event("base_game_data_update", {"accepted_methods": ["do_stand", "do_double", "do_hit"]}, conn_context.websocket)
            # draw event rewrite
            # ! TODO add do deal, now only create_bet processing
            await self.broadcast(players, "users_update", {"user_data": conn_context.player.to_dict(), "draw_event": f"{conn_context.player.publick_name} сделал ставку!"})
            
            ...
        ...
    
    async def __process_do_stand(self, data: dict, conn_context: ConnectionContext):
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            ...     
        ...

    async def __process_do_double(self, data: dict, conn_context: ConnectionContext):
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            ...     
        ...

    async def __process_do_hit(self, data: dict, conn_context: ConnectionContext):
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            ...     
        ...
        
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
        
    async def broadcast(self, clients_ids: list[int], event_type: str, data: dict):
        try:
            for client_id in clients_ids:
                await self.send_event(event_type, data, self.ws_connections[client_id])
        except asyncio.exceptions.CancelledError:
            pass
        
