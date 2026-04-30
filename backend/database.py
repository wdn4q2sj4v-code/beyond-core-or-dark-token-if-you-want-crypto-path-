"""
Database setup for the BEYOND backend.

Provides a SQLAlchemy engine, session factory (``SessionLocal``) and
declarative ``Base`` class shared by all models.  A SQLite database is used
by default so the service can run without any external infrastructure.  Set
the ``DATABASE_URL`` environment variable to override this.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./beyond.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
