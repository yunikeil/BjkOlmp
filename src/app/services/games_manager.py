from typing import Literal
from dataclasses import dataclass
from json.decoder import JSONDecodeError

from pydantic import ValidationError
from fastapi import Depends, Header, WebSocket, WebSocketException, status

from core.bj_game import bj_core
from core.redis import get_redis_client, get_redis_pipeline


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
    ws_connections: dict[str, set[WebSocket]] = {}
    rooms: dict[bj_core.GameRoom, set[str]] = {}

    def __init__(self):
        pass
        
    async def __call__(
        self,
        websocket: WebSocket,
        ws_type = Header("text", alias="Connection-Type")
    ):
        player = bj_core.RoundPlayer()
        return ConnectionContext(websocket, player, ws_type), self

    async def __raise(
        self, conn_context: ConnectionContext, code: int, reason: str | None = None
    ):
        await self.disconnect(conn_context)
        raise WebSocketException(code, reason)

    async def connect(self, conn_context: ConnectionContext):
        await conn_context.websocket.accept()
        self.ws_connections[conn_context.player.id] = conn_context.websocket
        
        await conn_context.websocket.send_json(
            {
                "player_id": conn_context.player.id
            }
        )
        
        
        
    async def disconnect(self, conn_context: ConnectionContext):
        del self.ws_connections[conn_context.player.id]
        
        for room, players in self.rooms.items():
            if conn_context.player.id not in players:
                continue
            
            room.remove_player(conn_context.player)
            await self.broadcast()
            break
    
    def __find_opened_room(self, player: bj_core.RoundPlayer) -> str | None:
        """
        Ищет и автоматически добавляет игрока в существующую игру
        """
        for room in self.rooms.keys():
            if not room.is_need_player():
                continue
            
            room.add_player(player)
            self.rooms[room].add(player.id)
            return room.id
    
    def __create_room(self, player: bj_core.RoundPlayer, max_players: int = 1):
        """
        Создаёт новую игру
        """
        new_room = bj_core.GameRoom(max_players)
        new_room.add_player(player)
        self.rooms[new_room] = {player.id}
        return new_room.id
    
    def __start_game(self, room_id: str):
        for room in self.rooms.keys():
            if room.id != room_id:
                continue
            
            room.start_game()
            break
    
    async def __process_find_game(self, data: dict, conn_context: ConnectionContext):
        game_type: Literal["new", "old"] = data.get("game_type")
        match game_type:
            case "new":
                max_players = data.get("max_players")
                room_id = self.__create_room(conn_context.player, max_players)
            case "old":
                room_id = self.__find_opened_room(conn_context.player)
                if not room_id:
                    max_players = data.get("max_players", 2)
                    room_id = self.__create_room(conn_context.player, max_players)
        
        await conn_context.websocket.send_json({"room_id": room_id})
    
    async def __process_event_type(
        self,
        event: Literal[
            "find_game",
            "start_game"
        ],
        data: dict,
        conn_context: ConnectionContext
    ):
        match event:
            case "find_game":
                await self.__process_find_game(data, conn_context)
   
    async def listen_event(
        self, conn_context: ConnectionContext
    ):
        player, websocket = conn_context.unpack()
        client_data: dict = await websocket.receive_json()
        event_type: str = client_data.get("event")
        data: dict = client_data.get("data")
        
        await self.__process_event_type(event_type, data, conn_context)
        
    async def broadcast(self, clients_ids: list[int], data: dict):
        
        ...
