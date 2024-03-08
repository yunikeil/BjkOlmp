from core.utils.text_colors import *
from core.utils.text_process import *
from core.utils.mytypes import CardSuit


host = "localhost:8000"

# / \
# | |
# \ /

console_main_page = r"""\
 ________________________________________________________________________________
Добро пожаловать на сайт {}Карточной игры «Блек-джек»{}. Я вижу вы тут впервые,
давайте вместе всё настроим и.. вы используете {}{}{}!? Хотя как корова может видеть...
Если я угадала, введите команду для установки клиента - {}wget http://localhost:8000/inst{}{}
Если не угадала, введите эту - {}wget http://localhost:8000/inst{}{}
 -------------------------------------------------------------------------------
{}        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----{}w{}{} |
                ||     ||{}
""".format(
    bold,
    reset,
    blue,
    "{var_system}",
    reset,
    yellow,
    "{fext}",
    reset,
    yellow,
    "{_fext}",
    reset,
    bold,
    pink,
    reset,
    bold,
    reset,
)

browser_main_page = """
Я пока в разработке, давайте попробуйем в консольке?
"""

main_pages: dict[str, str] = {
    "windows": console_main_page,
    "linux": console_main_page,
    "browser": browser_main_page,
}


console_about_linux_page = frame_text(
    """
    Данная программа была разработана
    в рамках задания полуфинала для 
    олимпиады траектория будущего
    """,
    max_len=33,
)

console_about_windows_page = """
"""

cards_suits: dict[CardSuit, str] = {
    "hearts": "♥",  # червы
    "diamonds": "♦",  # бубны
    "clubs": "♣",  # трефы
    "spades": "♠",  # пики
}
