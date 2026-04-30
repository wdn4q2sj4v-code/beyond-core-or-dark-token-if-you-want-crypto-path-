from fastapi import FastAPI

from database import Base, engine
from routers.governance import router as governance_router

# Create all tables on startup (mirrors Alembic for development; use
# proper Alembic migrations in production).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BEYOND", version="0.1.0")

app.include_router(governance_router)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
