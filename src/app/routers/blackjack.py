import os

from fastapi import Depends, APIRouter, WebSocketDisconnect
from fastapi.responses import FileResponse

from core.settings import config
from app.services.games_manager import GameConnectionManager, ConnectionContext


ws_router = APIRouter(prefix="/ws")
game_manager = GameConnectionManager()


@ws_router.websocket("/blackjack/")
async def game_connections(ws_context_data: tuple[ConnectionContext, GameConnectionManager] = Depends(game_manager)):
    conn_context, conn_manager = ws_context_data
    await conn_manager.connect(conn_context)
    
    try:
        while True:
            await conn_manager.listen_event(conn_context)
    except WebSocketDisconnect:
        await conn_manager.disconnect(conn_context)
