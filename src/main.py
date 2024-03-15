import logging

import uvicorn
import fastapi

from core.settings import config
from app.routers import root_router
from app.routers import inst_router
from app.routers import ws_blck_router


logger = logging.getLogger("uvicorn")

async def lifespan(app: fastapi.FastAPI):
    
    ...
    
    yield
    
    ...


app = fastapi.FastAPI(
    debug=config.DEBUG,
    lifespan=lifespan,
)
app.include_router(root_router)
app.include_router(inst_router)
app.include_router(ws_blck_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, proxy_headers=not config.DEBUG)


