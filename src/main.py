import logging

import uvicorn
import fastapi

from core.redis import redis_pool, get_redis_client
from core.settings import config
from app.routers import root_router
from app.routers import inst_router
from app.routers import ws_blck_router


logger = logging.getLogger("uvicorn")

async def lifespan(app: fastapi.FastAPI):
    
    async with get_redis_client() as client:
        logger.info(f"Redis ping returned with: {await client.ping()}.")

    yield
    
    await redis_pool.aclose()
    logger.info("RedisPool closed.")


app = fastapi.FastAPI(
    debug=config.DEBUG,
    lifespan=lifespan,
)
app.include_router(root_router)
app.include_router(inst_router)
app.include_router(ws_blck_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)


