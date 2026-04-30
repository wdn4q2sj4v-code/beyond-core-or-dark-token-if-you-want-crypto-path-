from fastapi import FastAPI

from .database import Base, engine
from .routers import governance_override

# Creates tables automatically for local development.
# In production, use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BEYOND API")

app.include_router(governance_override.router)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
