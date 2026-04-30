"""
Database base class and session factory for the app package.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://beyond_user:beyond_password@localhost:5432/beyond",
)

if DATABASE_URL.startswith("sqlite"):
    raise RuntimeError("SQLite is disabled")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
