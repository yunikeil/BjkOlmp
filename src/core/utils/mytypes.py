from typing import Literal


clients = Literal[
    "browser",
    "windows",
    "linux"
]


def reverse_client(client: clients) -> clients:
    if client == "windows":
        return "linux"
    
    return "windows"

