# # flake8: noqa


# from typing import Literal, List, Dict
# from dataclasses import dataclass

# CardNumber = Literal[
#     "Aces", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"
# ]
# CardSuit = Literal["heart", "diamond", "club", "spade"]

# # TODO Выбор вариантов отображения карт


# """

#                                _
#        ,'`.    _  _    /\    _(_)_
#       (_,._)  ( `' )  <  >  (_)+(_)
#         /\     `.,'    \/      |
#                                _
#        ,db.                  _(M)_
#       (MMMM)       Stef     (M)+(M)
#         db                     |


#                                      _____
#          _____                _____ |6    |
#         |2    | _____        |5    || ^ ^ |
#         |  ^  ||3    | _____ | ^ ^ || ^ ^ | _____
#         |     || ^ ^ ||4    ||  ^  || ^ ^ ||7    |
#         |  ^  ||     || ^ ^ || ^ ^ ||____9|| ^ ^ | _____
#         |____Z||  ^  ||     ||____S|       |^ ^ ^||8    | _____
#                |____E|| ^ ^ |              | ^ ^ ||^ ^ ^||9    |
#                       |____h|              |____L|| ^ ^ ||^ ^ ^|
#                                                   |^ ^ ^||^ ^ ^|
#                                                   |____8||^ ^ ^|
#                                                          |____6|

# """
# # https://en.m.wikipedia.org/wiki/Playing_cards_in_Unicode

# CARDS_NUMBERS: List[CardNumber] = [
#     "Ace",
#     "2",
#     "3",
#     "4",
#     "5",
#     "6",
#     "7",
#     "8",
#     "9",
#     "10",
#     "Jack",
#     "Queen",
#     "King",
# ]
# CARDS_WEIGHT: Dict[CardNumber, int] = {
#     "Aces": [11, 1, ],
#     "2": [2, 2, ],
#     "3": [3, 3, ],
#     "4": [4, 4, ],
#     "5": [5, 5, ],
#     "6": [6, 6, ],
#     "7": [7, 7, ],
#     "8": [8, 8, ],
#     "9": [9, 9, ],
#     "10": [10, 10, ],
#     "Jack": [10, 10, ],
#     "Queen": [10, 10, ],
#     "King": [10, 10, ],
# }
# CARDS_SUITS: Dict[CardSuit, str] = {
#     "heart": "♥",    # червы
#     "diamond": "♦", # бубны
#     "club": "♣",     # трефы
#     "spade": "♠",    # пики
# }

# # len - 11
# VIEW_CARD = """\
# ┌─────────┐
# │         │
# │         │
# │         │
# │         │
# │         │
# │         │
# │         │
# └─────────┘
# """


# @dataclass
# class Card:
#     number: CardNumber
#     suit: CardSuit

#     def to_text(self):
#         suit_symbol = CARDS_SUITS[self.suit]
#         if self.number in ["10", "King"]:
#             suit_symbol = suit_symbol.upper()
#         rank = self.number if self.number == '10' else self.number[0]
#         return VIEW_CARD.format(rank=rank, suit=suit_symbol)


# card_0 = Card("2", "diamond")
# card_1 = Card("Aces", "heart")

# print(card_0.to_text())




# #!/usr/bin/env python
# '''
# A Python class implementing KBHIT, the standard keyboard-interrupt poller.
# Works transparently on Windows and Posix (Linux, Mac OS X).  Doesn't work
# with IDLE.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as 
# published by the Free Software Foundation, either version 3 of the 
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# '''

# import os

# # Windows
# if os.name == 'nt':
#     import msvcrt

# # Posix (Linux, OS X)
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


# def fold_strings(string: str, string_: str):
#     result_lines = []
#     lines_0 = string.splitlines()
#     lines_1 = string_.splitlines()
    
#     for line_0, line_1 in zip(lines_0, lines_1):
#         result_lines.append(line_0 + " " +line_1)
    
#     if len(lines_0) > len(lines_1):
#         result_lines.extend(lines_0[len(lines_1):])
#     elif len(lines_1) > len(lines_0):
#         result_lines.extend(lines_1[len(lines_0):])
    
#     return "\n".join(result_lines)

# print(fold_strings("Hello\nMy\n", "World\n"))



# import curses
# from curses import wrapper

# def draw_card(stdscr, y, x, card):
#     """Отображает карту на экране."""
#     stdscr.addstr(y, x, card)

# def draw_interface(stdscr, player_cards, dealer_cards):
#     """Отображает интерфейс игры."""
#     # Очищаем экран
#     stdscr.clear()
    
#     # Отображаем карты игрока
#     for i, card in enumerate(player_cards):
#         draw_card(stdscr, 2 + i, 2, card)
    
#     # Отображаем карты дилера
#     for i, card in enumerate(dealer_cards):
#         draw_card(stdscr, 2 + i, 20, card)
    
#     # Отображаем кнопки действий
#     stdscr.addstr(10, 2, "Hit")
#     stdscr.addstr(10, 10, "Stand")
#     stdscr.addstr(10, 18, "Quit")
    
#     stdscr.refresh()

# def main(stdscr):
#     # Инициализация игры
#     player_cards = ["A♠", "K♥"]
#     dealer_cards = ["10♣", "J♦"]
    
#     while True:
#         draw_interface(stdscr, player_cards, dealer_cards)
        
#         # Ожидаем нажатия клавиши пользователем
#         key = stdscr.getch()
        
#         if key == ord('h'):
#             # Добавляем карту игроку
#             player_cards.append("J♠")
#         elif key == ord('s'):
#             # Игрок стоит
#             break
#         elif key == ord('q'):
#             # Выход из игры
#             break


# import curses
# import time

# # Инициализация окна
# screen = curses.initscr()
# curses.curs_set(0) # Скрыть курсор

# # Отрисовка анимации
# for i in range(50):
#     screen.clear()
#     screen.addstr(10, i, "x")
#     screen.refresh()
#     time.sleep(0.1)

# # Завершение работы с curses
# curses.endwin()


# import asyncio
# import threading

# class KeyboardThread(threading.Thread):
#     def __init__(self, input_cbk=None, name='keyboard-input-thread'):
#         self.input_cbk = input_cbk
#         super(KeyboardThread, self).__init__(name=name)
#         self.start()

#     def run(self):
#         while True:
#             self.input_cbk(input()) # Ожидает ввода + Return

# def my_callback(inp):
#     # Обработка ввода с клавиатуры
#     print('Вы ввели:', inp)

# # Запуск потока для чтения ввода с клавиатуры
# kthread = KeyboardThread(my_callback)

# async def main():
#     while True:
#         print(111)
#         await asyncio.sleep(1) # Пример асинхронной задержки

# if __name__ == "__main__":
#     asyncio.run(main())
