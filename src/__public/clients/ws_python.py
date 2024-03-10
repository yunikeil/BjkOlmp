import asyncio
import json
import functools
import websockets
import asyncio
from typing import Literal
from dataclasses import dataclass
from json.decoder import JSONDecodeError

import sys
import curses
import uuid


BASE_URI = "ws://localhost:8000/ws/blackjack/"

tasks: set[asyncio.Task] = set()

def async_exit_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (ConnectionRefusedError, websockets.exceptions.ConnectionClosedError):
            print("cant connect to server, exiting")
            for task in tasks:
                task.cancel()
            exit()

    
    return wrapper


@dataclass
class Card:
    weight: str
    suit: str


@dataclass
class Player:
    publick_name: str
    cards: list[Card] = None
    
    def add_cards(self, cards: list[Card]):
        """
        Добавляет карты игроку
        """
        for card in cards:
            self.cards.append(card)
            
    def draw(self):
        print(f"Имя: {self.publick_name}")
        print(f"Кол-во карт: {len(self.cards) if self.cards else 0}")


class BaseGameBJ:
    def __init__(self, ws: websockets.WebSocketClientProtocol) -> None:
        self.server = ws
        # base game data
        self.is_started: bool = False
        self.max_players: int = 3 # пока вручную
        self.ws_id = None

        # users_update   # user_update
        self.players: list[Player] = [Player("Me")]

    async def __disconnect(self) -> None:
        await self.server.close_connection()
    
    async def __send_json(self, data: dict) -> None:
        await self.server.send(json.dumps(data))
    
    async def __receive_json(self) -> dict:
        data = json.loads(await self.server.recv())
        await asyncio.sleep(0)
        return data
    
    async def __process_users_update(self, data: dict):
        print("    |data| users_update", data)
        
        draw_event = None
        if player_name := data.get("connected"):
            self.players.append(Player(player_name))
            draw_event = data
        elif player_name := data.get("disconnected"):
            for player in self.players:
                if player.publick_name == player_name:
                    self.players.remove(player)
                    draw_event = data
                    break
        
        if not self.is_started:
            await self.check_wait_players()
            
        return draw_event
            
    async def __process_base_game_data_update(self, data: dict):
        print("    |data| base_game_data_update", data)
        for key, value in data.items():
            setattr(self, key, value)
        
    async def __process_event_type(self, event: str, data: dict):
        match event:
            case "users_update":
                draw_event = await self.__process_users_update(data)
            case "base_game_data_update":
                draw_event = await self.__process_base_game_data_update(data)
        
        await self.draw_game(draw_event)

    async def __start_listen_ws_events(self):
        while True:
            server_data = await self.__receive_json()
            event_type = server_data.get("event")
            data = server_data.get("data")
            
            await self.__process_event_type(event_type, data)

    async def connect(self):
        self.ws_id = (await self.__receive_json()).get("player_id")
        t = asyncio.create_task(self.__start_listen_ws_events())
        tasks.add(t)
        
    async def create_new_round(self):
        await self.__send_json(
            {
                "event": "find_game",
                "data": {
                    "game_type": "new",
                    "max_players": 3
                }
            }
        )

    async def find_old_round(self):
        await self.__send_json(
            {
                "event": "find_game",
                "data": {
                    "game_type": "new",
                    "max_players": 3
                }
            }
        )
    
    async def start_game(self):
        await self.__send_json(
            {
                "event": "start_game",
            }
        )
    
    async def check_wait_players(self):
        if len(self.players) == self.max_players:
            await self.start_game()
    
    async def draw_game(self, draw_event: dict = {}):
        print("================================== next_list ==================================")#os.system("clear")
        if not self.is_started:
            print("Ожидание игроков...")
            print("Игроков в лобби:", len(self.players))
            for player in self.players:
                print("------------")
                player.draw()
            return
        elif self.is_started:
            if draw_event:
                if gm := draw_event.get("")
                elif nm := draw_event.get("disconnected"):
                    print(f"Кажется {nm} покинул игру, печально!")
            print("Игра идёт!")
            print("Игроков в лобби:", len(self.players))
            for player in self.players:
                print("------------")
                player.draw()
            return

# !TODO серв часть обработка вертание карт
# TODO(when) основа готова (need) рефактор

def n_input(msg, default = None):
    if not (default is None):
        print(msg + str(default))
        return default
    
    return input(msg)

import os


async def main():
    print("================================== next_list ==================================")
    print("Привет это игра блек джек!")
    v = int(n_input("Создать комнату/присоединиться? [0/1]: ", 0))
    
    async with websockets.connect(BASE_URI) as ws:
        game = BaseGameBJ(ws)
        await game.connect()
        
        if v:
            await game.create_new_round()
        else:
            await game.find_old_round()
        
        print("================================== next_list ==================================")
        
        while True:

            
            await asyncio.sleep(0.1)



asyncio.run(main())





"""
# Скобочки для скрытия в редакторе

# Ниже содержание других тестовых файлов, может пригодиться
# Надеюсь историю гита не будет никто читать :)

# #! khbit base переписать под нужды

# import os

# if os.name == 'nt':
#     import msvcrt
# else:
#     import sys
#     import termios
#     import atexit
#     from select import select


# class KBHit:
#     def __init__(self):
#         if os.name == 'nt':
#             pass
#         else:
#             self.fd = sys.stdin.fileno()
#             self.new_term = termios.tcgetattr(self.fd)
#             self.old_term = termios.tcgetattr(self.fd)

#             self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
#             termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

#             atexit.register(self.set_normal_term)


#     def set_normal_term(self):
#         if os.name == 'nt':
#             pass
#         else:
#             termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


#     def getch(self):
#         s = ''
#         if os.name == 'nt':
#             return msvcrt.getch().decode('utf-8')
#         else:
#             return sys.stdin.read(1)


#     def getarrow(self):
#         ''' Returns an arrow-key code after kbhit() has been called. Codes are
#         0 : up
#         1 : right
#         2 : down
#         3 : left
#         Should not be called in the same program as getch().
#         '''

#         if os.name == 'nt':
#             msvcrt.getch() # skip 0xE0
#             c = msvcrt.getch()
#             vals = [72, 77, 80, 75]
#         else:
#             c = sys.stdin.read(3)[2]
#             vals = [65, 67, 66, 68]

#         return vals.index(ord(c.decode('utf-8')))


#     def kbhit(self):
#         if os.name == 'nt':
#             return msvcrt.kbhit()
#         else:
#             dr,dw,de = select([sys.stdin], [], [], 0)
#             return dr != []


# if __name__ == "__main__":
#     kb = KBHit()
#     print('Hit any key, or ESC to exit')
#     while True:
#         if kb.kbhit():
#             c = kb.getch()
#             if ord(c) == 27:
#                 break
#             print(c)

#     kb.set_normal_term()


# ! curses example of code 


# import curses
# import time

# screen = curses.initscr()
# curses.curs_set(0)

# for i in range(50):
#     screen.clear()
#     screen.addstr(10, i, "x")
#     screen.refresh()
#     time.sleep(0.1)

# curses.endwin()


# ! \t\r example 


# import time

# def print_percent_done(index, total, bar_len=50, title='Please wait'):
#     percent_done = (index+1)/total*100
#     percent_done = round(percent_done, 1)

#     done = round(percent_done/(100/bar_len))
#     togo = bar_len-done

#     done_str = '█'*int(done)
#     togo_str = '░'*int(togo)

#     print(f'\t⏳{title}: [{done_str}{togo_str}] {percent_done}% done', end='\r')

#     if round(percent_done) == 100:
#         print('\t✅')


# r = 50
# for i in range(r):
#     print_percent_done(i,r)
#     time.sleep(0.02)

"""