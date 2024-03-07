from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import PlainTextResponse

from core.depends import get_type_client
from core.utils.content import main_pages 
from core.utils.mytypes import clients, reverse_client


router = APIRouter()


@router.get("/")
async def root_page(client: clients = Depends(get_type_client)):
    return PlainTextResponse(main_pages[client].format(var_system=client, _var_system=reverse_client(client)))
