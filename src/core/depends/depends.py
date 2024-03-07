from random import choice

from fastapi import Depends
from fastapi import Request

from core.utils.mytypes import clients


# TODO Добавить проверку в бд ip:client (есть вероятность, что зайдет через браузер сначала)

def get_type_client(request: Request) -> clients:
    if not (usag := request.headers.get("user-agent", None)):
        usag = request.headers.get("User-Agent", None)
    
    relevant = ["windows", "linux"]

 
    if "curl" in usag:
        # Ну а как cowsay должна увидеть |
        #          тут тип клиента?     / 
        # 'user-agent': 'curl/8.4.0' <=| 
        return choice(relevant)
    
    if usag:
        return "browser"
    
    return "linux"
