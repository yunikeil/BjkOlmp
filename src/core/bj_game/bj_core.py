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


@dataclass
class Card:
    weight: CardNumber
    suit: CardSuit

    def to_dict(self):
        return {"weight": self.weight, "suit": self.suit}

    def to_text(self):
        weight = self.weight if self.weight == "10" else self.weight[0]
        return VIEW_CARD.format(
            weight=weight, weight_=REVERS_WEIGHT[weight], suit=CARDS_SUITS[self.suit]
        )

    @staticmethod
    def hidden():
        return HIDDEN_CARD


class BasePlayer:
    def __init__(self) -> None:
        self._cards: list[Card] = []

    def add_cards(self, cards: list[Card]):
        """
        Добавляет карты игроку
        """
        for card in cards:
            self._cards.append(card)

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
        for card in self._cards:
            points += CARDS_WEIGHT[card.weight][0]
        if points <= limit:
            return points

        points = 0
        for card in self._cards:
            points += CARDS_WEIGHT[card.weight][1]

        return points

    def cards_to_text(self, need_hidden: bool):
        """
        Преобразует массив карт в линейную строку для вывода
        """
        card_lines = [*[card.to_text().splitlines() for card in self._cards]]
        if need_hidden:
            card_lines = [*[HIDDEN_CARD.splitlines()], *card_lines[1:]]

        max_lines = max(len(lines) for lines in card_lines)
        padded_lines = [lines + [""] * (max_lines - len(lines)) for lines in card_lines]
        transposed_lines = list(zip(*padded_lines))
        return "\n".join("".join(line for line in lines) for lines in transposed_lines)


class RoundPlayer(BasePlayer):
    """
    Класс отвечающий за игрока
    """

    def __init__(self, publick_name: str) -> None:
        self.loose_points: int = 0
        self.win_points: int = 0
        self.is_last_win: bool = False
        self.__gamer_bank = 5000
        self.__current__bet: int = -1
        self.is_move_over = False
        self.publick_name: str = publick_name
        self.id: str = uuid.uuid4().hex

        super().__init__()

    def to_dict(self):
        return {
            "loose_points": self.loose_points,
            "win_points": self.win_points,
            "is_last_win": self.is_last_win,
            "cards": [card.to_dict() for card in self._cards],
            "gamer_bank": self.__gamer_bank,
            "current_bet": self.__current__bet,
            "is_move_over": self.is_move_over,
            "publick_name": self.publick_name,
        }
    
    def lose_bet(self):
        # Проигрышь
        self.is_last_win = False
        self.loose_points += self.__current__bet
        self.__current__bet = 0
    
    def win_bet(self):
        # Победа
        self.is_last_win = True
        self.win_points += self.__current__bet
        self.__gamer_bank += self.__current__bet
        self.__current__bet = 0
    
    def draw_bet(self):
        # Ничья
        self.is_last_win = None
        self.__gamer_bank += self.__current__bet
        self.__current__bet = 0

    def _create_bet(self, bet: int):
        bet = abs(bet)

        if self.__current__bet != -1:
            raise ValueError("Ставка уже создана")
        
        if self.__gamer_bank < bet:
            raise ValueError("Нехватка денег на счёте")

        self.__gamer_bank -= bet
        self.__current__bet = bet

    def _double_bet(self):
        if self.__gamer_bank < self.__current__bet:
            raise ValueError("Нехватка денег на счёте")

        if len(self._cards) > 2:
            raise ValueError("Удвоить можно только в начале раунда")

        if self.is_move_over:
            raise ValueError("Ход был закончен")
                
        self.__gamer_bank -= self.__current__bet
        self.__current__bet *= 2

    def cards_to_text(self):
        return super().cards_to_text(need_hidden=False)


class RoundDealer(BasePlayer):
    """
    Класс отвечающий за диллера
    """
    def __init__(self, publick_name: str) -> None:
        self.publick_name: str = publick_name
        self.is_move_over = False

        super().__init__()


    def to_dict(self):
        return {"cards": [card.to_dict() for card in self._cards],  "publick_name": self.publick_name, "is_move_over": self.is_move_over}

    def cards_to_text(self, need_hidden: bool = True):
        return super().cards_to_text(need_hidden=need_hidden)


class GameRoom:
    def __init__(self, max_players: int) -> None:
        self.__available_cards: list[Card] = self.__construct_decks(max_players * 2)
        self.__wagered_cards: list[Card] = []
        self.__shuffle_cards()

        self.__max_players: int = max_players
        self.__players: list[RoundPlayer] = []
        self.results: dict[str, str] = {}
        self.__dealer: RoundDealer = RoundDealer("DealerBoss")
        self.is_round_finished: bool = False
        self.is_started: bool = False
        self.id: str = uuid.uuid4().hex

    def to_dict(self):
        return {
            "wagered_cards": [card.to_dict() for card in self.__wagered_cards],
            "max_players": self.__max_players,
            "players": [player.to_dict() for player in self.__players],
            "dealer": self.__dealer.to_dict(),
            "is_started": self.is_started,
            "id": self.id
        }

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

    def _calculate_payments(self):
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
        # Предполагаем, что у нас есть метод get_dealer_points для получения очков дилера
        dealer_points = self.__dealer.get_points()
                
        for player in self.__players:
            player_points = player.get_points()
            
            if player_points > 21:
                player.lose_bet()
                print(f"{player.publick_name} lose")
                
            elif dealer_points > 21:
                player.win_bet()
                print(f"{player.publick_name} win")

            elif player_points > dealer_points:
                player.win_bet()
                print(f"{player.publick_name} win")

                
            elif player_points < dealer_points:
                player.lose_bet()
                print(f"{player.publick_name} lose")
                
            else:
                player.draw_bet()
                print(f"{player.publick_name} draw")
            
            print("prin is win", player.is_last_win)
            print("win points", player.win_points)
            print("loose points", player.loose_points)
            print()
            print()


    
    def if_all_with_cards_add_cards_to_dealer(self):
        for player in self.__players:
            if len(player._cards) < 1:
                return
        
        self.__dealer.add_cards(self.__get_random_cards(2))
        return self.__dealer

    def do_deal(self, player: RoundPlayer, bet: int):
        # Делаем ставку, с получением карт (1)
        player._create_bet(bet)
        player.add_cards(self.__get_random_cards(2))
        
        if player.get_points() >= 21:
            player.is_move_over = True
            return True
        
        return False

    def do_stand(self, player: RoundPlayer) -> bool:
        # Игрок завершает раунд оставляет текущее кол-во очков
        # Диллер добавляет себе карты пока ещё счёт не станет больше 16
        player.is_move_over = True

    def do_double(self, player: RoundPlayer) -> bool:
        # Игрок удваивает ставку с запросом новой карты
        # Работает только после превого хода
        player._double_bet()
        player.add_cards(self.__get_random_cards())
        
        if player.get_points() >= 21:
            player.is_move_over = True
            return True
        
        return False
        
    def do_hit(self, player: RoundPlayer):
        # Игрок просит новую карту, можно делать пока не будет > 21
        player.add_cards(self.__get_random_cards())
        
        if player.get_points() >= 21:
            player.is_move_over = True
            return True
        
        return False
    
    def check_is_all_players_standed(self):
        for player in self.__players:
            if not player.is_move_over:
                return False
        
        self.__dealer.is_move_over = True
        while self.__dealer.get_points() < 17:
            self.__dealer.add_cards(self.__get_random_cards())
        
        self.is_round_finished = True
        
        self._calculate_payments()
        
        return self.__dealer