from fastapi import FastAPI

import models
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
