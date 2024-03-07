import uvicorn
import fastapi

from app.routers import root_router


app = fastapi.FastAPI()
app.include_router(root_router)



if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)



