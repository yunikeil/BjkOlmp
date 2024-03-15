import os
import json
import time
import asyncio
import functools
from typing import Literal

import websockets
from dataclasses import dataclass


# Адрес сервера
BASE_URI = "ws://localhost:8000/ws/blackjack/"
BASE_CLIENT_WIDTH=121
# Список асинхронных задач, если таковые есть
TASKS: set[asyncio.Task] = set()
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
bold = "\033[1m"
pink = "\033[38;2;255;105;180m"
red = "\033[31m"
green = "\033[32m"
blue = "\033[34m"
yellow = "\033[33m"
reset = "\033[0m"
vars_c = [bold, red, green, blue, yellow, reset]


def blocking_wait(seconds: int, bar_len: int = 50, title: str = 'Пожалуйста подождите'):
    """
    Функция, для отрисовки загрузки в частности используется 
    на моментах, когда пользователю нужно рассмотреть какую-либо информацию
    """
    seconds *= 10
    for index in range(seconds):
        percent_done = (index+1)/seconds*100
        percent_done = round(percent_done, 1)

        done = round(percent_done/(100/bar_len))
        togo = bar_len-done

        done_str = '█'*int(done)
        togo_str = '░'*int(togo)

        print(f'\t⏳ {title}: [{done_str}{togo_str}] {percent_done}% выполнено', end='\r')

        if round(percent_done) == 100:
            print('\t✅ ')
        
        time.sleep(0.1)


async def nb_wait(seconds: int, bar_len: int = 50, title: str = 'Пожалуйста подождите'):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, blocking_wait, seconds, bar_len, title)
    return result


def async_exit_handler(func):
    """
    Декоратор для единого перехвата ошибок в асинхронных функциях
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (ConnectionRefusedError, websockets.exceptions.ConnectionClosedError):
            print("cant connect to server, exiting")
            for task in TASKS:
                task.cancel()
            exit()

    return wrapper


async def n_b_input(msg = None, default = None):
    """ 
    Неблокирующая функция ввода
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, n_input, msg, default)
    return result


def n_input(msg = None, default = None):
    """
    Функция ввода со стандратным значением
    """
    if not (default is None):
        print(msg + str(default))
        return default
    elif msg is None and default is None:
        return input()
    return input(msg)


def fold_strings(string: str, string_: str):
    result_lines = []
    lines_0 = string.splitlines()
    lines_1 = string_.splitlines()
    
    for line_0, line_1 in zip(lines_0, lines_1):
        result_lines.append(line_0 + " " +line_1)
    
    if len(lines_0) > len(lines_1):
        result_lines.extend(lines_0[len(lines_1):])
    elif len(lines_1) > len(lines_0):
        result_lines.extend(lines_1[len(lines_0):])
    
    return "\n".join(result_lines)
fs = fold_strings


def find_len(text: str) -> int:
    """ 
    Считает чистую длину строки, без ansi символов
    """
    for ansi_color in vars_c:
        text = text.replace(ansi_color, "")

    return len(text)


def frame_text(text: str, max_len: str = BASE_CLIENT_WIDTH, use_list: bool = False, need_center: bool = True) -> str | list[str]:
    """
    Обворачивает предоставленный текс в рамку
    """
    result = []
    if not text:
        return None
    
    lines = text.splitlines()
    max_line_length = max(find_len(line) for line in lines)
    buff = "┌" + "─" * (max_line_length + 2) + "┐"
    result.append(buff.center(max_len) if need_center else buff)
    for line in lines:
        buff = "│ " + line + " " * (max_line_length - find_len(line)) + " │"
        result.append(buff.center(max_len) if need_center else buff)

    buff = "└" + "─" * (max_line_length + 2) + "┘\n"
    result.append(buff.center(max_len) if need_center else buff)

    if not use_list:
        return "\n".join(result)

    return result
ft = frame_text


@dataclass
class Card:
    """
    dataclass для хранения информации о картах
    """
    weight: CardNumber
    suit: CardSuit

    @staticmethod
    def from_json(data: dict) -> "Card":
        """
        Метод используется для создания карты из dict объекта
        """
        return Card(**data)

    def to_text(self):
        """
        Превращаем данные в карте в текстовую строку
        """
        weight = self.weight if self.weight == "10" else self.weight[0]
        return VIEW_CARD.format(
            weight=weight, weight_=REVERS_WEIGHT[weight], suit=CARDS_SUITS[self.suit]
        )
    
    @staticmethod
    def hidden():
        """
        Просто удобный способ для получения скрытой карты
        """
        return HIDDEN_CARD

    def draw(self):
        """
        Отрисовывает карту
        """
        print(self.to_text())
    
    def draw_hidden(self):
        """
        Отрисовывает скрытую карту        
        """
        print(self.hidden())


@dataclass
class Player:
    """
    dataclass Игрока, имеет стандартные методы для ввода и вывода информации
    """
    bank: int
    bet: int
    publick_name: str
    is_move_over: bool = False
    cards: list[Card] = None
    loose_points: int = None
    win_points: int = None
    is_last_win: bool | None = None
    is_me: bool = None

    @staticmethod
    def from_json(data: dict) -> "Player":
        """ 
        Создаёт новый объект игрока из словаря
        """
        cards = []
        for card_json in data.get("cards", []):
            cards.append(Card.from_json(card_json))
            
        return Player(
            bank = data.get("gamer_bank"),
            bet = data.get("current_bet"),
            publick_name = data.get("publick_name"),
            is_move_over = data.get("is_move_over"),
            cards = cards,
            loose_points = data.get("loose_points"),
            win_points = data.get("win_points"),
            is_last_win = data.get("is_last_win"),
        )
    
    def update_from_json(self, data: dict):
        """
        Обновляет текущий объект из словаря
        """
        self.bank = data.get("gamer_bank")
        self.bet = data.get("current_bet")
                
        self.is_move_over = data.get("is_move_over")
        self.loose_points = data.get("loose_points"),
        self.win_points = data.get("win_points"),
        self.is_last_win = data.get("is_last_win"),

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
        if not self.cards:
            return None
        
        card_lines = [*[card.to_text().splitlines() for card in self.cards]]
        if need_hidden:
            card_lines = [*[HIDDEN_CARD.splitlines()], *card_lines[1:]]

        max_lines = max(len(lines) for lines in card_lines)
        padded_lines = [lines + [""] * (max_lines - len(lines)) for lines in card_lines]
        transposed_lines = list(zip(*padded_lines))
        return "\n".join("".join(line for line in lines) for lines in transposed_lines)
    
    def to_text(self, is_started: bool, is_dealer: bool = False, is_result: bool = False, need_cards: bool = False):
        """
        Используется для создания массива строк данного пользователя
        """
        lines = []
        lines.append(f"Имя: {'Me(' if self.is_me else ''}{self.publick_name}{')' if self.is_me else ''} ")
        lines.append(f"Текущая ставка: {self.bet}")
        lines.append(f"Текущий банк: {self.bank}")
        if is_result:
            lines.append(f"Выиграл всего: {self.win_points} ")
            lines.append(f"Проиграл всего: {self.loose_points} ")
            lines.append(f"Выиграл ли сейчас: {self.is_last_win} ")
            lines.append(f"Количество очков {self.get_points()} ")
            return "\n".join(lines)

        lines.append(f"Закончил ли ход: {self.is_move_over} ")
        if ((not is_dealer) or self.is_move_over) and self.cards:
            lines.append(f"Количество очков {self.get_points()} ")
        lines.append(f"Кол-во карт: {len(self.cards) if self.cards else 0} ")
        if need_cards:
            if is_started and self.cards:
                lines.append(self.cards_to_text(True if (is_started and is_dealer and not self.is_move_over) else False))
        
        return "\n".join(lines)

    def draw_cards(self, need_hidder: bool = False):
        """
        Отрисовывает только карты игрока
        """
        print(self.cards_to_text(need_hidder))
                    
    def draw(self, is_started: bool, is_dealer: bool = False, is_result: bool = False):
        """
        Отрисовывает игрока полностью
        """
        print(f"Имя: {'Me(' if self.is_me else ''}{self.publick_name}{')' if self.is_me else ''}")
        print(f"Текущая ставка: {self.bet}")
        print(f"Текущий банк: {self.bank}")
        if is_result:
            print(f"Выиграл всего: {self.win_points}")
            print(f"Проиграл всего: {self.loose_points}")
            print(f"Выиграл ли сейчас: {self.is_last_win}")
            return

        print(f"Закончил ли ход: {self.is_move_over}")
        if ((not is_dealer) or self.is_move_over) and self.cards:
            print(f"Количество очков {self.get_points()}")
        print(f"Кол-во карт: {len(self.cards) if self.cards else 0}")
        if is_started and self.cards:
            self.draw_cards(True if (is_started and is_dealer and not self.is_move_over) else False)


class BaseGameBJ:
    """
    Базовый класс для управления игрок
    """
    def __init__(self, ws: websockets.WebSocketClientProtocol, max_players: int = -1) -> None:
        self.server = ws
        self.queue_inputs: list[str] = []
        self.me_pub_name = None
        self.is_round_finished: bool = False
        self.is_started: bool = False # (Game)
        self.max_players: int = max_players
        self.ws_id = None
        self.players: list[Player] = []
        self.dealer: Player = Player(bank=None, bet=None, publick_name="DealerBoss")
        
        self.all_server_methods: dict = {
            "do_deal": [self.do_deal, "Сделать ставку"],
            "do_stand": [self.do_stand, "Закончить ход"],
            #"do_split": ...,
            "do_double": [self.do_double, "Удвоить ставку"],
            "do_hit": [self.do_hit, "Взять карту"],
        }
        self.accepted_methods: list = []

    async def __disconnect(self) -> None:
        """
        Отключения от вебсоккета
        """
        await self.server.close_connection()
    
    async def __send_json(self, data: dict) -> None:
        """
        Отправка словаря в вебсоккет
        """
        await self.server.send(json.dumps(data))
    
    async def __receive_json(self) -> dict:
        """
        Получение словаря из вебсоккета
        """
        data = json.loads(await self.server.recv())
        return data

    def find_player(self, publick_name):
        """
        Поиск игрока по публичному имени
        """
        for player in self.players:
            if player.publick_name == publick_name:
                return player
        
    async def __process_users_update(self, data: dict):
        """
        Обработка ивента users_update
        """
        
        draw_event = None
        if player_name := data.get("connected", False):
            self.players.append(Player(bank=5000, bet=-1, publick_name=player_name, is_move_over=False))
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
        """
        Обработка ивента dealer_update
        """ 

        dealer_data = data.get("dealer_data")
        self.dealer.update_from_json(dealer_data)

                    
    async def __process_base_game_data_update(self, data: dict):
        """
        Обработка ивента base_game_data_update
        """
        for key, value in data.items():
            setattr(self, key, value)
            
    async def _process_game_data_update(self, data: dict):
        """
        Обработка ивента game_data_update
        """
        self.max_players = data.get("max_players")
        for player_json in data.get("players", []):
            pl = Player.from_json(player_json)
            self.players.append(pl)
        
        self.dealer = Player.from_json(data.get("dealer"))
        self.is_started = data.get("is_started")
        asyncio.create_task(nb_wait(5, title="Начинаем игру"))
    
    async def __process_full_game_data_update(self, data: dict):
        """ 
        Обработка ивента full_game_data_updat
        """
        self.max_players = data.get("max_players")
        self.players = []
        for player_json in data.get("players", []):
            pl = Player.from_json(player_json)
            if pl.publick_name == self.me_pub_name:
                pl.is_me = True
                self.players.insert(0, pl)
            else:
                self.players.append(pl)
                
        self.dealer = Player.from_json(data.get("dealer"))
        self.is_started = data.get("is_started")
        self.is_round_finished = data.get("is_round_finished")
                        
    async def __process_event_type(self, event: str, data: dict):
        """
        Получение ивента и дальнейшая отправка для обработки
        """      
        match event:
            case "game_data_update":
                # Полное обновление всех полей
                # Происходит когда клиент (1) ПРИСОЕДИНЯЕТСЯ к комнате
                await self._process_game_data_update(data)
            case "users_update":
                # Обновление юзеров 
                # Происходит когда в комнату кто-либо заходит или выходит
                await self.__process_users_update(data)
            case "dealer_update":
                await self.__process_dealer_update(data)
            case "base_game_data_update":
                # Частичное заполнение полей например 
                # при первичном подключении к серверу
                # или при СОЗДАНИИ новой комнаты
                # или при начале игры (is_started)
                await self.__process_base_game_data_update(data)
            case "full_game_data_update":
                await self.__process_full_game_data_update(data)
        

    async def __start_listen_ws_events(self):
        """
        listener для приходящих с сервера ивентов
        """
        # try:
        while True:
            server_data = await self.__receive_json()
            server_dict: list[dict] = server_data.get("events")
            draw_event = server_data.get("draw_event", None)
            for event_data in server_dict:
                event_type = event_data.get("event_type")
                data = event_data.get("data")
                                                            
                await self.__process_event_type(event_type, data)
                        
            await self.draw_game(draw_event)
        # except websockets.exceptions.ConnectionClosedError:
        #     print("\nВероятно сервер перезапускается, перезагрузите клиент\n")
        #     exit()
        # except websockets.exceptions.ConnectionClosedOK as e:
        #     print("\nВыключаем клиент...\n")
        #     raise e
        #     exit()
        # except asyncio.exceptions.CancelledError:
        #     exit()
        # except BaseException as e:
        #     print(f"\nНеизвестная ошибка: {type(e)}, выходим из клиента...\n")
        #     exit()

    async def connect(self):
        """
        Подключение клиента (не вебсоккета) к серверу
        """
        conn_data: dict = (await self.__receive_json())["events"][0]["data"]
        self.ws_id = conn_data.get("player_id")
        self.me_pub_name = conn_data.get("my_name")
        self.players.append(Player(bank=5000, bet=-1, publick_name=conn_data.get("my_name"), is_me=True))
        asyncio.gather(self.__start_listen_ws_events())#!, return_exceptions=True)
        
    async def create_new_round(self):
        """
        Отправляем на сервер ивент для создания новой комнаты
        """
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
        """
        Отправляем на сервер ивент для поиска уже созданной
        """
        await self.__send_json(
            {
                "event": "find_game",
                "data": {
                    "game_type": "old",
                }
            }
        )
    
    async def start_game(self):
        """
        Отправляем на сервер ивент для начала игры
        """
        #blocking_wait(10)
        await self.__send_json(
            {
                "event": "start_game",
            }
        )
        asyncio.create_task(nb_wait(5, title="Начинаем игру"))
    
    async def do_deal(self) -> tuple:
        """
        Обрабатываем пользовательский ввод, отправляем на сервер ивент
        """
        bet = int(await self.process_input_command("Введите ставку: ", processor=n_b_input))
        
        await self.__send_json(
            {
                "event": "do_deal",
                "data": {
                    "bet": bet
                }
            }
        )

    async def do_stand(self) -> bool:
        """
        Отправляем на сервер ивент о том, что игрок завершил ход
        Игрок завершает раунд оставляет текущее кол-во очков (2)
        Диллер добавляет себе карты пока ещё счёт не станет больше 16
        """
        await self.__send_json(
            {
                "event": "do_stand",
            }
        )
    
    async def do_double(self):
        """
        Отправляем на сервер ивент о том, что игрок удвоил ставку
        Игрок удваивает ставку с запросом новой карты
        Работает только после превого хода
        """
        await self.__send_json(
            {
                "event": "do_double",
            }
        )

    async def do_hit(self):
        """
        Отправляем на сервер ивент о том, что игрок просит карту
        Игрок просит новую карту, можно делать пока не будет > 21
        """
        await self.__send_json(
            {
                "event": "do_hit",
            }
        )
    
    async def check_wait_players(self):
        """
        Проверяем, если комната полная, начинаем игру
        Единственный метод, который полнятся с клиентской обработкой
        Перенести на сервер не хватает времени, хотя и занимает данное действие
         крайне маленькое количество времени
        """
        if len(self.players) == self.max_players:
            await self.start_game()
    
    async def process_input_command(self, question = None, processor = None, *args):
        """
        Обрабатываем команды, которые поступают от пользователя
        Данный метод делался с заделом на будущее (планировалась поддержка ввода/вывода curses а также msvcrt)
        В идеале для обработки ввода использовать общеизвестный пример khbit для языка python
        """     
        if not self.is_started:
            return

        if not self.accepted_methods:
            return
        
        if not question: # TODO переделать чудо
            pre_q = ""
            for i, method_name in enumerate(self.accepted_methods):
                descr = self.all_server_methods[method_name][1]
                pre_q += f"[{i}] :: {descr}\n"
            pre_q += f"Выберите требуемое действие [{0}-{len(self.accepted_methods)-1}]:"
            # pre_q = "Разрешенные действия: \n" + str(self.accepted_methods) + "\nВыберите индекс нужного действия: "
            # print(self.accepted_methods)
            print(pre_q, end=" ")
            self.queue_inputs.append(pre_q)
        else:
            print(question, end=" ")
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
        """
        Метод используемый для отрисовки класса game
        """
        os.system("clear")
        #print("================================== next_list ==================================")
        if draw_event:
            print(ft(draw_event))
        
        if not self.is_started:
            print(ft(f"Ожидание игроков, в лобби: {len(self.players)} "))
            for player in self.players:
                print(ft(player.to_text(self.is_started)))
        
        elif self.is_round_finished:
            print(ft("Раунд закончен! Результаты =>"))
            dealer_b = ft(self.dealer.to_text(self.is_started, True, True, need_cards=False), need_center=False)
            cards_b = self.dealer.cards_to_text(True)
            if cards_b:
                print(fs(dealer_b, cards_b))
            else:
                print(dealer_b)
            for player in self.players:
                player_b = ft(player.to_text(self.is_started, False, True, need_cards=False), need_center=False)
                cards_b_p =  player.cards_to_text()
                if cards_b_p:
                    print(fs(player_b, cards_b_p))
                else:
                    print(player_b)
            
            await nb_wait(10 * 2, title="Ознакомление с результатами")

        elif self.is_started:
            dealer_b = ft(self.dealer.to_text(self.is_started, True, need_cards=False), need_center=False)
            cards_b = self.dealer.cards_to_text(True)
            if cards_b:
                print(fs(dealer_b, cards_b))
            else:
                print(dealer_b)
            for player in self.players:
                player_b = ft(player.to_text(self.is_started, need_cards=False), need_center=False)
                cards_b_p =  player.cards_to_text()
                if cards_b_p:
                    print(fs(player_b, cards_b_p))
                else:
                    print(player_b)
        
    
        if self.queue_inputs:
            print(self.queue_inputs[-1], end=" ")

        # print()
        # print("================================== next_list ==================================")#os.system("clear")
        # if draw_event:
        #     print(draw_event)

        # if not self.is_started:
        #     print("Ожидание игроков...")
        #     print("Игроков в лобби:", len(self.players))
        #     for player in self.players:
        #         print("------------")
        #         player.draw(self.is_started)
                
        # elif self.is_round_finished:
        #     print("Раунд закончен. Результаты:")
        #     print("Диллер: ")
        #     self.dealer.draw(self.is_started, True, True)
        #     for player in self.players:
        #         print("------------")
        #         player.draw(self.is_started, False, True)
        #     print("------------")
                
        # elif self.is_started:            
        #     print("Игра идёт!")
        #     print("Игроков в лобби:", len(self.players))
        #     print("Диллер: ")
        #     self.dealer.draw(self.is_started, True)
        #     for player in self.players:
        #         print("------------")
        #         player.draw(self.is_started)
        # print("------------")
        
        # if self.queue_inputs:
        #     print(self.queue_inputs[-1])


async def main():
    """
    Главная функция клиента, в которой происходит первоначальная настройка и обработка пользовательского ввода
    Серверная сторона также должна была поддерживать работу с чистым текстом (клиент отвечает за вывод и ввод)
     без дополнительного упрощения в json (для этого была предусмотрен один из header параметров: Connection-Type)
     также можно ставить свои никнеймы с использование дополнительного параметра Publick-Name.
    Однако от этого пришлось отказаться из-за нехватки времени, хотя времени данные изменения не будут привносить
    Также в проекте существует много проблем с определением ивентов, к примеру, неоднозначные наименования
    Изначально предполагалась одиночная игра и консольный мини-сайтик, но в процессе было решено переписать на
     онлайн игру, это вызвало проблемы не только с определением ивентов, но и в других частях.
    Как простейший вариант исправления, можно использовать лишь один метод обновления сразу всех данных, т.к. данные
     на клиента обновляются довольно редко, это могло бы сильно упростить как разработку так и чтение кода...
    """
    #try:
    os.system("clear")
    hello_message = "Если игра неправильно отображается в консоли, попробуйте сделать её шире\n"
    hello_message += "Базовая ширина консоли составляет около 120 символов, интерфейс рассчитан 124 символа. "
    print(ft(hello_message))
    print(ft("Привет это игра блек джек! Пожалуйста, выберите вариант игры ниже\n"))
    v = int(n_input("Создать комнату/присоединиться? [0/1]:".center(BASE_CLIENT_WIDTH).rstrip() + " "))

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
    
    # except asyncio.exceptions.CancelledError:
    #     pass
    # except websockets.exceptions.ConnectionClosedError:
    #     print("Внутренняя ошибка сервера или прокси сервера, попробуйте позже...")
    #     exit()
    # except ConnectionRefusedError:
    #     print(f"Не удалось подключиться к серверу, попробуйте позже..")
    #     exit()
    # except KeyboardInterrupt:
    #     print()
    #     exit()
    # except ValueError:
    #     print("Пожалуйста, вводите корректные данные, не стоит устраивать 'проверки на дурака'")
    #     print("Выходим из клиента, перезапустите его для продолжения...")
    #     exit()
    # except BaseException as e:
    #     print(f"\nНеизвестная ошибка: {type(e)}, выходим из клиента..")
    #     exit()

        
asyncio.run(main())
