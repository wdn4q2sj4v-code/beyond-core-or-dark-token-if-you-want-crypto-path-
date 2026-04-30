"""
Database base class and session factory for the app package.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://beyond:beyond@localhost:5432/beyond",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Yield a database session and ensure it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
