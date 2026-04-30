from fastapi import FastAPI

from backend.routers import admin

app = FastAPI()

app.include_router(admin.router)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
