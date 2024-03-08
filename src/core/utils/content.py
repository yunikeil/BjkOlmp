import textwrap

from core.utils.text_colors import * 
from core.utils.text_process import *

host = "localhost:8000" 

# / \
# | |
# \ /

console_main_page = \
rf"""
 ________________________________________________________________________________
Добро пожаловать на сайт {bold}Карточной игры «Блек-джек»{reset}. Я вижу вы тут впервые,
давайте вместе всё настроим и.. вы используете {blue}{'{var_system}'}{reset}!? Хотя как корова может видеть...
Если я угадала, введите команду для установки клиента - {yellow}curl http://localhost:8000/clients/installer/installer{'{fext}'}{reset}
Если не угадала, введите эту - {yellow}curl http://localhost:8000/clients/installer/installer{'{_fext}'}{reset}
 -------------------------------------------------------------------------------
{bold}        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----{pink}w{reset}{bold} |
                ||     ||{reset}
""".removeprefix("\n")

browser_main_page = \
"""
Я пока в разработке, давайте попробуйем в консольке?
"""

main_pages: dict[str, str] = {"windows": console_main_page, "linux": console_main_page, "browser": browser_main_page}


console_about_linux_page = frame_text(
    """
    Данная программа была разработана
    в рамках задания полуфинала для 
    олимпиады траектория будущего
    """, max_len=33
)

console_about_windows_page = """
"""


