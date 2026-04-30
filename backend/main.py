from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
from routers import admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(admin.router)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
