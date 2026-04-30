from fastapi import FastAPI

from governance import router as governance_router

app = FastAPI(title="BEYOND Core API")

app.include_router(governance_router)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
