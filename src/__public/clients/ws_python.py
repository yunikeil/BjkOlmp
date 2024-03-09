import asyncio
import json
import functools
import websockets
import asyncio
from typing import Literal
from dataclasses import dataclass
from json.decoder import JSONDecodeError

import curses
import uuid


BASE_URI = "ws://localhost:8000/ws/blackjack/"


def async_exit_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ConnectionRefusedError:
            print("cant connect to server")
    
    return wrapper


class BaseGameBJ:
    def __init__(self, ws: websockets.WebSocketClientProtocol) -> None:
        self.server = ws
        self.is_started: bool
        self.player_id: int
        self.room_id: int

    async def __disconnect(self) -> None:
        await self.server.close_connection()
    
    async def __send_json(self, data: dict) -> None:
        await self.server.send(json.dumps(data))
    
    async def __receive_json(self) -> dict:
        data = json.loads(await self.server.recv())
        await asyncio.sleep(0)
        return data

    async def __process_users_update(self, data):
        print(data)
        ...
    
    async def __process_event_type(self, event: str, data: dict):
        match event:
            case "users_update":
                await self.__process_users_update(data)
            case "data_update":
                await self.__process_users_update(data)

    async def __start_listen_ws_events(self):
        while True:
            server_data = await self.__receive_json()
            event_type = server_data.get("event")
            data = server_data.get("data")
            
            await self.__process_event_type(event_type, data)

    async def setup(self):
        self.player_id = (await self.__receive_json()).get("player_id")
        asyncio.create_task(self.__start_listen_ws_events())
    
    async def create_new_round(self):
        await self.__send_json(
            {
                "event": "find_game",
                "data": {
                    "game_type": "new",
                    "max_players": 2
                }
            }
        )

    async def find_old_round(self):
        await self.__send_json(
            {
                "event": "find_game",
                "data": {
                    "game_type": "new",
                    "max_players": 2
                }
            }
        )
    
    async def start_game(self):
        
        ...


def n_input(msg, default = None):
    if not (default is None):
        print(msg + str(default))
        return default
    
    return input(msg)


async def main():
    print("Привет это игра блек джек!")
    v = int(n_input("Создать комнату/присоединиться? [0/1]: ", 0))
    
    async with websockets.connect(BASE_URI) as ws:
        game = BaseGameBJ(ws)
        await game.setup()
        
        if v:
            await game.create_new_round()
        else:
            await game.find_old_round()
        
        
        while True:
            print(1)
            await asyncio.sleep(0.1)
        
                
asyncio.run(main())
