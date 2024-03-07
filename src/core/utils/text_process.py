import textwrap
from inspect import cleandoc

from core.utils.text_colors import vars_c


def find_len(text: str) -> int:
    for ansi_color in vars_c:
        text = text.replace(ansi_color, "")

    return len(text)


def frame_text(text: str, max_len: str, use_list: bool = False) -> str | list[str]:
    result = []

    lines = text.splitlines()
    max_line_length = max(find_len(line) for line in lines)
    buff = "┌" + "─" * (max_line_length + 2) + "┐"
    result.append(buff.center(max_len))
    for line in lines:
        buff = "│ " + line + " " * (max_line_length - find_len(line)) + " │"
        result.append(buff.center(max_len))

    buff = "└" + "─" * (max_line_length + 2) + "┘\n"
    result.append(buff.center(max_len))

    if not use_list:
        return "\n".join(result)

    return result

