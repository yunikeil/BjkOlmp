# flake8: noqa


from typing import Literal, List, Dict
from dataclasses import dataclass

CardNumber = Literal[
    "Aces", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"
]
CardSuit = Literal["heart", "diamond", "club", "spade"]

# TODO Выбор вариантов отображения карт


"""

                               _
       ,'`.    _  _    /\    _(_)_
      (_,._)  ( `' )  <  >  (_)+(_)
        /\     `.,'    \/      |
                               _
       ,db.                  _(M)_
      (MMMM)       Stef     (M)+(M)
        db                     |


                                     _____
         _____                _____ |6    |
        |2    | _____        |5    || ^ ^ |
        |  ^  ||3    | _____ | ^ ^ || ^ ^ | _____
        |     || ^ ^ ||4    ||  ^  || ^ ^ ||7    |
        |  ^  ||     || ^ ^ || ^ ^ ||____9|| ^ ^ | _____
        |____Z||  ^  ||     ||____S|       |^ ^ ^||8    | _____
               |____E|| ^ ^ |              | ^ ^ ||^ ^ ^||9    |
                      |____h|              |____L|| ^ ^ ||^ ^ ^|
                                                  |^ ^ ^||^ ^ ^|
                                                  |____8||^ ^ ^|
                                                         |____6|

"""
# https://en.m.wikipedia.org/wiki/Playing_cards_in_Unicode

CARDS_NUMBERS: List[CardNumber] = [
    "Ace",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "Jack",
    "Queen",
    "King",
]
CARDS_WEIGHT: Dict[CardNumber, int] = {
    "Aces": [11, 1, ],
    "2": [2, 2, ],
    "3": [3, 3, ],
    "4": [4, 4, ],
    "5": [5, 5, ],
    "6": [6, 6, ],
    "7": [7, 7, ],
    "8": [8, 8, ],
    "9": [9, 9, ],
    "10": [10, 10, ],
    "Jack": [10, 10, ],
    "Queen": [10, 10, ],
    "King": [10, 10, ],
}
CARDS_SUITS: Dict[CardSuit, str] = {
    "heart": "♥",    # червы
    "diamond": "♦", # бубны
    "club": "♣",     # трефы
    "spade": "♠",    # пики
}

# len - 11
VIEW_CARD = """\
┌─────────┐
│         │
│         │
│         │
│         │
│         │
│         │
│         │
└─────────┘
"""


@dataclass
class Card:
    number: CardNumber
    suit: CardSuit

    def to_text(self):
        suit_symbol = CARDS_SUITS[self.suit]
        if self.number in ["10", "King"]:
            suit_symbol = suit_symbol.upper()
        rank = self.number if self.number == '10' else self.number[0]
        return VIEW_CARD.format(rank=rank, suit=suit_symbol)


card_0 = Card("2", "diamond")
card_1 = Card("Aces", "heart")

print(card_0.to_text())