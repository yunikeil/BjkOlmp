import uuid
from typing import Literal
from random import shuffle, choice
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
        return VIEW_CARD.format(weight=weight, weight_=REVERS_WEIGHT[weight], suit=CARDS_SUITS[self.suit])

    @staticmethod
    def hidden():
        return HIDDEN_CARD


class HumanBaseBJ:
    def __init__(self) -> None:
        self.__cards: list[Card]
    
    def add_cards(self, cards: list[Card]):
        """
        Добавляет карты игроку
        """
        for card in cards:
            self.__cards.append(card)

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
        for card in self.__cards:
            points += CARDS_WEIGHT[card.weight][0]
        if points <= limit:
            return points

        points = 0
        for card in self.__cards:
            points += CARDS_WEIGHT[card.weight][1]

        return points
    
    def cards_to_text(self, need_hidden: bool):
        """
        Преобразует массив карт в линейную строку для вывода
        """
        card_lines = [*[card.to_text().splitlines() for card in self.__cards]]
        if need_hidden:
            card_lines = [*[HIDDEN_CARD.splitlines()], *card_lines[1:]]
        
        max_lines = max(len(lines) for lines in card_lines)
        padded_lines = [lines + [""] * (max_lines - len(lines)) for lines in card_lines]
        transposed_lines = list(zip(*padded_lines))
        return "\n".join("".join(line for line in lines) for lines in transposed_lines)


class RoundPlayer(HumanBaseBJ):
    """
    Класс отвечающий за игрока
    """
    def __init__(self) -> None:
        self.__gamer_bank = 5000
        self.__current__bet: int
        self.id: str = uuid.uuid4().hex
        
        super().__init__()
    
    def create_bet(self, bet: int):
        bet = abs(bet)
        
        if self.__gamer_bank < bet:
            raise ValueError("Нехватка денег на счёте")
        
        self.__gamer_bank -= bet
        self.__current__bet = bet
    
    def double_bet(self):
        if self.__gamer_bank < self.__current__bet:
            raise ValueError("Нехватка денег на счёте")
        
        self.__gamer_bank -= self.__current__bet
        self.__current__bet *= 2
    
    def cards_to_text(self):
        return super().cards_to_text(need_hidden=False)


class RoundDealer(HumanBaseBJ):
    """
    Класс отвечающий за диллера
    """

    def cards_to_text(self, need_hidden: bool = True):
        return super().cards_to_text(need_hidden=need_hidden)


class GameRoom:
    def __init__(self, max_players: int) -> None:
        self.__available_cards: list[Card] = self.__construct_decks(max_players * 2)
        self.__wagered_cards: list[Card] = []
        self.__shuffle_cards()
        
        self.__max_players: int = max_players
        self.__players: list[RoundPlayer] = []
        self.__dealer: RoundDealer = None
        self.is_started: bool = False
        self.id: str = uuid.uuid4().hex
    
    def is_need_player(self) -> bool:
        if self.is_started:
            return False
        if len(self.__players) < self.__max_players:
            return True
        return False
        
    def add_player(self, player: RoundPlayer):
        self.__players.append(player)
    
    def remove_player(self, player: RoundPlayer):
        self.__players.remove(player)

    def start_game(self):
        self.is_started = True
    
    def __shuffle_cards(self):
        shuffle(self.__available_cards)
    
    def __construct_decks(self, number_of_decks):
        deck = []
        for _ in range(number_of_decks):
            for suit in CARDS_SUITS:
                for number in CARDS_WEIGHT.keys():
                    deck.append(Card(number, suit))
        
        return deck

    def __get_random_cards(self, number_of_cards: int = 1) -> list[Card]:
        cards = []
        for _ in range(number_of_cards):
            card = choice(self.__available_cards)
            self.__available_cards.remove(card)
            self.__wagered_cards.append(card)
            cards.append(card)

        return cards
        
    def _end_current_round(self):
        
        ...
    
    def _calculate_payment(
        self, 
        situation: Literal[
            "black_jack",
            "player_bust",
            
        ]
    ):
        """
        # Сначала все игроки должны завершить ход далее идёт подсчёт
        player_jack - игрок получает 1.5 его ставки
        dealer_jack - все у кого не black_jack теряют ставки
        player_bust - игрок теряет ставку
        """
        
        ...
    
    def _calculate_status(self):
        """
        Простейшая проверка, можно усложнить, добавив полный свод правил
        К примеру проверка на то выпал ли туз у диллера для более верного
        Получения суждений о том, получил ли пользовать Black-Jack
        >>> Если у игрока сразу после раздачи набралось 21 очко 
         (то есть у игрока туз и десятиочковая карта), то такая 
         ситуация и называется блек-джек. В таком случае игроку сразу
         выплачивается выигрыш 3 к 2 (то есть в 1,5 раза превышающий его ставку).
         Исключение составляют случаи, когда дилеру первой картой (открытой) 
         попадается 10, картинка или туз. В этом случае существует вероятность, 
         что у дилера также будет блек-джек, поэтому игроку с блек-джеком предлагается 
         либо взять выигрыш 1 к 1 (только если первая карта дилера — туз), либо дождаться
         окончания конца игры (и в случае, если у дилера не блек-джек, получить выигрыш 3 к 2).
        """
        
        ...
        
    def get_gamedate(self) -> dict:
        
        ...
              

    def do_deal(self, bet: int) -> tuple:
        
        ...        

    def do_stand(self) -> bool:
        # Игрок завершает раунд оставляет текущее кол-во очков
        # Диллер добавляет себе карты пока ещё счёт не станет больше 16
        ...            
        
    def do_double(self):
        # Игрок удваивает ставку с запросом новой карты
        # Работает только после превого хода
        
        ...

    def do_hit(self):
        # Игрок просит новую карту, можно делать пока не будет > 21

        ...

