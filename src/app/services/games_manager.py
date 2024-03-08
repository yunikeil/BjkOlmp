# import uuid
# from dataclasses import dataclass
# from json.decoder import JSONDecodeError

# from pydantic import ValidationError
# from fastapi import WebSocket, WebSocketException, status

# #from core.utils.mytypes import CardNumber, CardSuit
# #from core.utils.content import cards_suits

# @dataclass(frozen=True)
# class ConnectionContext:
#     """
#     websocket: WebSocket
#     is_auth_user: bool
#     unique_id: str
#     """

#     websocket: WebSocket
#     unique_id: str

#     def unpack(self):
#         return self.unique_id, self.websocket


# class GameConnectionManager:
#     ws_connections: dict[str, WebSocket] = {}

#     def __init__(self):
#         pass

#     def __call__(
#         self,
#         websocket: WebSocket,
#     ):
#         unique_id = uuid.uuid4().hex
#         return ConnectionContext(websocket, unique_id), self

#     async def __raise(
#         self, conn_context: ConnectionContext, code: int, reason: str | None = None
#     ):
#         await self.disconnect(conn_context)
#         raise WebSocketException(code, reason)

#     async def connect(self, conn_context: ConnectionContext):
#         await conn_context.websocket.accept()
#         self.ws_connections[conn_context.unique_id] = conn_context.websocket

#     async def disconnect(self, conn_context: ConnectionContext):
#         del self.ws_connections[conn_context.unique_id]

#     async def broadcast(
#         self, conn_context: ConnectionContext
#     ):
#         pass

#     async def start_listening(self, conn_context: ConnectionContext):
#         game_id, websocket = conn_context.unpack()
#         while True:
#             z = await websocket.receive_json()
#             print(z)


from random import shuffle, choice
from typing import Literal
from dataclasses import dataclass


# len - 11
VIEW_CARD = """\
┌─────────┐
│ {}      │
│         │
│    {}   │
│         │
│      {} │
└─────────┘
""".format('{weight: <2}', '{suit: <2}', '{weight_: >2}')
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


@dataclass
class Card:
    weight: CardNumber
    suit: CardSuit

    def to_text(self):
        weight = self.weight if self.weight == "10" else self.weight[0]
        formatters = []

        return VIEW_CARD.format(weight=weight, weight_=REVERS_WEIGHT[weight], suit=CARDS_SUITS[self.suit])

    @staticmethod
    def hidden():
        return HIDDEN_CARD


@dataclass
class GameRound:
    player_cards: list[Card]
    dealer_cards: list[Card]
    bet: int
    """
    Непонятно по заданию в каком случае туз становится 1
    Если перебор случился по его вине или в любом случае
    Я реализовал так, что туз становиться 1 при переборе в любом из случаев
    Вообще тем, кто писал эти задания отдельный привет, чтоб у вас все заказчики так ТЗ писали
    В попытках найти информацию в сети интернет найдено было целое ничего.
    В поисках экспертного мнения был обнаружен знакомый, проигравший 400кР в казино
    К сожалению он решил оставить данный вопрос без комментариев.
    """
    @staticmethod
    def __add_cards(desk: list[Card], cards: list[Card]):
        for card in cards:
            desk.append(card)

    def add_player_cards(self, cards: list[Card]):
        self.__add_cards(self.player_cards, cards)
    
    def add_dealer_cards(self, cards: list[Card]):
        self.__add_cards(self.dealer_cards, cards)

    @staticmethod
    def get_points_by_cards(cards: list[Card], limit: int = 21) -> int:
        # Не лучшее, но довольно простое решение
        #  к примеру улучшить можно добавив if points >= 11
        #  однако в таком случае пропадёт возможность менять
        #  вес остальных карт
        points = 0
        for card in cards:
            points += CARDS_WEIGHT[card.weight][0]
        if points <= limit:
            return points

        points = 0
        for card in cards:
            points += CARDS_WEIGHT[card.weight][1]

        return points

    def get_player_points(self):
        return self.get_points_by_cards(self.player_cards)

    def get_dealer_points(self):
        return self.get_points_by_cards(self.dealer_cards)

    @staticmethod
    def cards_to_text(cards: list[Card], need_hidden: bool = False):
        card_lines = [*[card.to_text().splitlines() for card in cards]]
        if need_hidden:
            card_lines = [*[HIDDEN_CARD.splitlines()], *card_lines]
        
        max_lines = max(len(lines) for lines in card_lines)
        padded_lines = [lines + [""] * (max_lines - len(lines)) for lines in card_lines]
        transposed_lines = list(zip(*padded_lines))
        return "\n".join("".join(line for line in lines) for lines in transposed_lines)
    
    def player_cards_to_text(self):
        return self.cards_to_text(self.player_cards)
    
    def dealer_cards_to_text(self):
        return self.cards_to_text(self.dealer_cards[1:], True)

"""
# Чекнуть по времени многопользовательский режим
"""
class GameCore:
    def __init__(self, number_of_decks: int = 1, gamer_bank: int = 5000) -> None:
        self.__available_cards: list[Card] = self.__construct_decks(number_of_decks)
        self.__wagered_cards: list[Card] = []
        self.gamer_bank = gamer_bank
        shuffle(self.__available_cards)

        self.round_number: int = 0
        self.__is_round_finished: bool = True
        self.__current_round: GameRound = None

    def __construct_decks(self, number_of_decks):
        deck = []
        for _ in range(number_of_decks):
            for suit in CARDS_SUITS:
                for number in CARDS_WEIGHT.keys():
                    deck.append(Card(number, suit))

        return deck

    def __deal_bet(self, bet: int) -> int:
        # Делаем ставку (после можно переделать на точное число с фишками)
        self.gamer_bank -= bet

    def __get_random_cards(self, number_of_cards: int = 1) -> list[Card]:
        cards = []
        for _ in range(number_of_cards):
            card = choice(self.__available_cards)
            self.__available_cards.remove(card)
            self.__wagered_cards.append(card)
            cards.append(card)

        return cards
    
    def get_gamedate() -> dict:
        
        ...
              

    def do_deal(self, bet: int) -> tuple:
        if not self.__is_round_finished:
            raise ValueError("Необходимо завершить предыдущий раунд")

        self.__deal_bet(bet)
        
        player_cards = self.__get_random_cards(2)
        dealer_cards = self.__get_random_cards(2)
        self.__current_round = GameRound(player_cards, dealer_cards, bet)
        self.__is_round_finished = False
        self.round_number += 1
        
        return (self.do_stand, self.do_double, self.do_hit)
        

    def do_stand(self) -> bool:
        # Игрок завершает раунд оставляет текущее кол-во очков
        # Диллер добавляет себе карты пока ещё счёт не станет больше 16
        if self.__is_round_finished:
            raise ValueError("Необходимо начать новый раунд")
        
        while self.__current_round.get_dealer_points() <= 16:
            self.__current_round.add_dealer_cards(self.__get_random_cards())
        
        ...
            
        
    def do_double(self):
        # Игрок удваивает ставку с запросом новой карты
        # Работает только после превого хода
        if self.__is_round_finished:
            raise ValueError("Необходимо начать новый раунд")
        
        ...

    def do_hit(self):
        # Игрок просит новую карту, можно делать пока не будет > 21
        if self.__is_round_finished:
            raise ValueError("Необходимо начать новый раунд")

        ...       

game = GameCore()
next_steps = game.do_deal(50)

gd = game.get_game_data()
print(f"""\
банк игрока: {game.gamer_bank}
ставка игрока: {gd.bet}
поинты диллера: ???
карты диллера:
{gd.dealer_cards_to_text()}
поинты игрока: {gd.get_player_points()}
карты игрока:
{gd.player_cards_to_text()}
""")
