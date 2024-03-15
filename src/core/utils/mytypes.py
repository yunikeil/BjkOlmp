from typing import Literal


Clients = Literal[
    "browser",
    "windows",
    "linux"
]


def reverse_client(client: Clients) -> Clients:
    if client == "windows":
        return "linux"
    
    return "windows"


CardNumber = Literal["Aces", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
CardSuit = Literal["hearts", "diamonds", "clubs", "spades"]