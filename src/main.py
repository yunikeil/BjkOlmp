import uvicorn
import fastapi

from app.routers import root_router
from app.routers import inst_router
#from app.routers import ws_blck_router


app = fastapi.FastAPI()
app.include_router(root_router)
app.include_router(inst_router)
#app.include_router(ws_blck_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)


