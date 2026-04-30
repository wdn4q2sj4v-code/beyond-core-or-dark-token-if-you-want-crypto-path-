import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from routers.admin import router as admin_router

app = FastAPI()

app.include_router(admin_router)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
