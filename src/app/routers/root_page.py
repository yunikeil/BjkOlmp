from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import PlainTextResponse

from core.depends import get_type_client
from core.utils.content import main_pages 


router = APIRouter()


file_extensions = {
    "linux": {
        "ext": ".sh && bash inst.sh",
        "_ext": ".ps1"
    },
    "windows": {
        "ext": ".ps1",
        "_ext": ".sh && bash inst.sh"
    }
}

@router.get("/")
async def root_page(client: str = Depends(get_type_client)):
    ext = file_extensions.get(client, file_extensions["windows"])["ext"]
    _ext = file_extensions.get(client, file_extensions["windows"])["_ext"]
    
    response_text = main_pages[client].format(var_system=client, fext=ext, _fext=_ext)
    return PlainTextResponse(response_text)
