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


# len - 11
VIEW_CARD = """\
┌─────────┐
│ {}      │
│         │
│    {}   │
│         │
│      {} │
└─────────┘
""".format(
    "{weight: <2}", "{suit: <2}", "{weight_: >2}"
)
HIDDEN_CARD = """\
┌─────────┐
│░░░░░░░░░│
│░░░░░░░░░│
│░░░░░░░░░│
│░░░░░░░░░│
│░░░░░░░░░│
└─────────┘
"""

CardNumber = Literal[
    "Aces", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"
]
CardSuit = Literal["heart", "diamond", "club", "spade"]

CARDS_WEIGHT: dict[CardNumber, int] = {
    "Aces": [11, 1],
    "2": [2, 2],
    "3": [3, 3],
    "4": [4, 4],
    "5": [5, 5],
    "6": [6, 6],
    "7": [7, 7],
    "8": [8, 8],
    "9": [9, 9],
    "10": [10, 10],
    "Jack": [10, 10],
    "Queen": [10, 10],
    "King": [10, 10],
}
REVERS_WEIGHT: dict[str, str] = {
    "A": "V",
    "2": "Z",
    "3": "E",
    "4": "h",
    "5": "S",
    "6": "9",
    "7": "L",
    "8": "8",
    "9": "6",
    "10": "0I",
    "J": "ɾ",
    "Q": "ᕹ",
    "K": "ʞ",
}
CARDS_SUITS: dict[CardSuit, str] = {
    "heart": "♥",  # червы
    "diamond": "♦",  # бубны
    "club": "♣",  # трефы
    "spade": "♠",  # пики
}


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

    @staticmethod
    def from_json(data: dict) -> "Card":
        return Card(
            data.get("weight"),
            data.get("suit")
        )

    def to_text(self):
        weight = self.weight if self.weight == "10" else self.weight[0]
        return VIEW_CARD.format(
            weight=weight, weight_=REVERS_WEIGHT[weight], suit=CARDS_SUITS[self.suit]
        )

    def draw(self):
        print(self.to_text())
    
    @staticmethod
    def draw_hidden():
        print(HIDDEN_CARD)


@dataclass
class Player:
    bank: int
    bet: int
    publick_name: str
    is_me: bool = None
    cards: list[Card] = None
    is_move_over: bool = False
    
    @staticmethod
    def from_json(data: dict) -> "Player":
        cards = []
        for card_json in data.get("cards", []):
            cards.append(Card.from_json(card_json))
            
        return Player(
            data.get("gamer_bank"),
            data.get("current_bet"),
            data.get("publick_name"),
            data.get("is_move_over"),
            cards
        )
    
    def update_from_json(self, data: dict):
        self.bank = data.get("gamer_bank")
        self.bet = data.get("current_bet")
        self.is_move_over = data.get("is_move_over")
        
        self.cards = []
        for card_json in data.get("cards", []):
            self.cards.append(Card.from_json(card_json))
                    
    def add_cards(self, cards: list[Card]):
        """
        Добавляет карты игроку
        """
        for card in cards:
            self.cards.append(card)
    
    def get_points(self, limit: int = 21) -> int:
        """
        Возвращает количество очков игрока
        """
        """
        Не лучшее, но довольно простое решение
         к примеру улучшить можно добавив if points >= 11
         однако в таком случае пропадёт возможность менять
         вес остальных карт
        Непонятно по заданию в каком случае туз становится 1
        Если перебор случился по его вине или в любом случае
        Я реализовал так, что туз становиться 1 при переборе в любом из случаев
        Вообще тем, кто писал эти задания отдельный привет, чтоб у вас все заказчики так ТЗ писали
        В попытках найти информацию в сети интернет найдено было целое ничего.
        В поисках экспертного мнения был обнаружен знакомый, проигравший 400кР в казино
        К сожалению он решил оставить данный вопрос без комментариев.
        """

        points = 0
        for card in self.cards:
            points += CARDS_WEIGHT[card.weight][0]
        if points <= limit:
            return points

        points = 0
        for card in self.cards:
            points += CARDS_WEIGHT[card.weight][1]

        return points

    def cards_to_text(self, need_hidden: bool = False):
        """
        Преобразует массив карт в линейную строку для вывода
        """
        card_lines = [*[card.to_text().splitlines() for card in self.cards]]
        if need_hidden:
            card_lines = [*[HIDDEN_CARD.splitlines()], *card_lines[1:]]

        max_lines = max(len(lines) for lines in card_lines)
        padded_lines = [lines + [""] * (max_lines - len(lines)) for lines in card_lines]
        transposed_lines = list(zip(*padded_lines))
        return "\n".join("".join(line for line in lines) for lines in transposed_lines)

    def draw_cards(self, need_hidder: bool = False):
        print(self.cards_to_text(need_hidder))
                    
    def draw(self, is_started: bool, is_dealer: bool = False):
        print(f"Имя: {'Me(' if self.is_me else ''}{self.publick_name}{')' if self.is_me else ''}")
        print(f"Текущая ставка: {self.bet}")
        print(f"Текущий банк: {self.bank}")
        print(f"Закончил ли ход: {self.is_move_over}")
        if ((not is_dealer) or self.is_move_over) and self.cards:
            print(f"Количество очков {self.get_points()}")
        print(f"Кол-во карт: {len(self.cards) if self.cards else 0}")
        if is_started and self.cards:
            self.draw_cards(True if (is_started and is_dealer and not self.is_move_over) else False)


# python src/__public/clients/ws_python.py


class BaseGameBJ:
    def __init__(self, ws: websockets.WebSocketClientProtocol, max_players: int = -1) -> None:
        self.server = ws
        self.queue_inputs: list[str] = []
        
        # base game data
        self.is_round_finished: bool = False
        self.is_started: bool = False # (Game)
        self.max_players: int = max_players
        self.ws_id = None

        # users_update   # user_update
        self.players: list[Player] = []
        self.dealer: Player = Player(None, None, "DealerBoss")
        
        self.all_server_methods: dict = {
            "do_deal": [self.do_deal],
            "do_stand": [self.do_stand],
            #"do_split": ...,
            "do_double": [self.do_double],
            "do_hit": [self.do_hit],
        }
        self.accepted_methods: list = []

    async def __disconnect(self) -> None:
        await self.server.close_connection()
    
    async def __send_json(self, data: dict) -> None:
        await self.server.send(json.dumps(data))
    
    async def __receive_json(self) -> dict:
        data = json.loads(await self.server.recv())
        await asyncio.sleep(0)
        return data

    def find_player(self, publick_name):
        for player in self.players:
            if player.publick_name == publick_name:
                return player
        
    async def __process_users_update(self, data: dict):
        print("    |data| users_update", data)   
        
        draw_event = None
        if player_name := data.get("connected", False):
            self.players.append(Player(5000, -1, player_name, False))
            draw_event = data
        
        elif player_name := data.get("disconnected", False):
            for player in self.players:
                if player.publick_name == player_name:
                    self.players.remove(player)
                    draw_event = data
                    break
        
        elif new_user_data := data.get("user_data", False):
            new_user_data: dict
            player = self.find_player(new_user_data.get("publick_name"))
            player.update_from_json(new_user_data)
            draw_event = new_user_data.get("draw_event", None)
            
        if not self.is_started:
            await self.check_wait_players()
            
        return draw_event
    
    async def __process_dealer_update(self, data: dict):
        print("    |data| dealer_update", data)   

        dealer_data = data.get("dealer_data")
        self.dealer.update_from_json(dealer_data)

                    
    async def __process_base_game_data_update(self, data: dict):
        print("    |data| base_game_data_update", data)
        for key, value in data.items():
            setattr(self, key, value)
            
    async def _process_game_data_update(self, data: dict):
        self.max_players = data.get("max_players")
        for player_json in data.get("players", []):
            pl = Player.from_json(player_json)
            self.players.append(pl)
        
        self.dealer = Player.from_json(data.get("dealer"))
        self.is_started = data.get("is_started")
        
    async def __process_event_type(self, event: str, data: dict):
        draw_event = None
        
        match event:
            case "game_data_update":
                # Полное обновление всех полей
                # Происходит когда клиент (1) ПРИСОЕДИНЯЕТСЯ к комнате
                draw_event = await self._process_game_data_update(data)
            case "users_update":
                # Обновление юзеров 
                # Происходит когда в комнату кто-либо заходит или выходит
                draw_event = await self.__process_users_update(data)
            case "dealer_update":
                draw_event = await self.__process_dealer_update(data)
            case "base_game_data_update":
                # Частичное заполнение полей например 
                # при первичном подключении к серверу
                # или при СОЗДАНИИ новой комнаты
                # или при начале игры (is_started)
                draw_event = await self.__process_base_game_data_update(data)
        
        return draw_event

    async def __start_listen_ws_events(self):
        while True:
            server_data = await self.__receive_json()
            event_type = server_data.get("event")
            data = server_data.get("data")
            need_draw = server_data.get("need_draw", True)
                        
            draw_event = await self.__process_event_type(event_type, data)
            
            if need_draw:
                await self.draw_game(draw_event)

    async def connect(self):
        conn_data: dict = (await self.__receive_json()).get("data")
        self.ws_id = conn_data.get("player_id")
        self.players.append(Player(5000, -1, conn_data.get("my_name"), True))
        asyncio.gather(self.__start_listen_ws_events())
        #tasks.add(t)
        
    async def create_new_round(self):
        await self.__send_json(
            {
                "event": "find_game",
                "data": {
                    "game_type": "new",
                    "max_players": self.max_players
                }
            }
        )

    async def find_old_round(self):
        await self.__send_json(
            {
                "event": "find_game",
                "data": {
                    "game_type": "old",
                    #"max_players": self.max_players
                }
            }
        )
    
    async def start_game(self):
        await self.__send_json(
            {
                "event": "start_game",
            }
        )
    
    async def do_deal(self) -> tuple:
        # Делаем ставку, с получением карт (1)
        bet = int(await self.process_input_command("Введите ставку", processor=n_b_input))
        
        await self.__send_json(
            {
                "event": "do_deal",
                "data": {
                    "bet": bet
                }
            }
        )

    async def do_stand(self) -> bool:
        # Игрок завершает раунд оставляет текущее кол-во очков (2)
        # Диллер добавляет себе карты пока ещё счёт не станет больше 16
        await self.__send_json(
            {
                "event": "do_stand",
            }
        )
    
    async def do_double(self):
        # Игрок удваивает ставку с запросом новой карты
        # Работает только после превого хода
        await self.__send_json(
            {
                "event": "do_double",
            }
        )

    async def do_hit(self):
        # Игрок просит новую карту, можно делать пока не будет > 21
        await self.__send_json(
            {
                "event": "do_hit",
            }
        )
    
    async def check_wait_players(self):
        # TODO Перенести на сторону сервера
        if len(self.players) == self.max_players:
            await self.start_game()
    
    async def process_input_command(self, question = None, processor = None, *args):        
        if not self.is_started:
            return

        if not self.accepted_methods:
            return
        
        if not question:
            pre_q = "Разрешенные действия: \n" + str(self.accepted_methods) + "\nВыберите индекс нужного действия: "
            print(pre_q)
            self.queue_inputs.append(pre_q)
        else:
            print(question)
            self.queue_inputs.append(question)

        if processor:
            command = await processor(*args)
        
        if not question:
            self.queue_inputs.remove(pre_q)
            await self.all_server_methods[self.accepted_methods[int(command)]][0]()
        else:
            self.queue_inputs.remove(question)
            return command
    
    async def draw_game(self, draw_event: dict = {}):
        print()
        print("================================== next_list ==================================")#os.system("clear")
        if not self.is_started:
            print("Ожидание игроков...")
            print("Игроков в лобби:", len(self.players))
            for player in self.players:
                print("------------")
                player.draw(self.is_started)
        elif self.is_round_finished:
            print("Раунд закончен. Результаты: ...")
                
        elif self.is_started:
            if draw_event:
                if nm := draw_event.get("disconnected"):
                    print(f"Кажется {nm} покинул игру, печально!")
            
            print("Игра идёт!")
            print("Игроков в лобби:", len(self.players))
            print("Диллер: ")
            self.dealer.draw(self.is_started, True)
            for player in self.players:
                print("------------")
                player.draw(self.is_started)
        print("------------")
        
        if self.queue_inputs:
            print(self.queue_inputs[-1])
        
        
 
# !TODO серв часть обработка вертание карт
# TODO(when) основа готова (need) рефактор

import asyncio
import concurrent.futures

async def n_b_input(msg = None, default = None):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, n_input, msg, default)
    return result


def n_input(msg = None, default = None):
    if not (default is None):
        print(msg + str(default))
        return default
    elif msg is None and default is None:
        return input()
    return input(msg)

import os
os.system("clear")

async def main():
    print("Привет это игра блек джек!")
    v = int(n_input("Создать комнату/присоединиться? [0/1]: "))
    
    async with websockets.connect(BASE_URI) as ws:
        game = BaseGameBJ(ws, 2)
        await game.connect()
        
        if not v:
            await game.create_new_round()
        else:
            await game.find_old_round()
        
        await game.check_wait_players()
        await asyncio.sleep(0.1)
        
        while True:
            await game.process_input_command(processor=n_b_input)
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