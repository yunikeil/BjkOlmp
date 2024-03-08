import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from core.settings import config
from core.utils.mytypes import clients

router = APIRouter(prefix="/clients")


# Переложить эту работу на nginx
# Временное решение для отладки

@router.get("/installer/{filename}")
async def root_page(filename: str):
    try:
        client_path = os.path.join(
            config.root_path, "src/__public/installers", filename
        )
        return FileResponse(client_path)
    except RuntimeError:
        raise HTTPException(404)

@router.get("/python/{filename}")
async def root_page(filename: str):
    try:
        client_path = os.path.join(
            config.root_path, "src/__public/clients", filename
        )
        return FileResponse(client_path)
    except RuntimeError:
        raise HTTPException(404)
