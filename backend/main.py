from fastapi import FastAPI

from .database import Base, engine
from .routers import admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BEYOND")

app.include_router(admin.router)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
