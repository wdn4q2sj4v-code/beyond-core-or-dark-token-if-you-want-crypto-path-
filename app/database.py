"""
Database base class and session factory for the app package.

The database URL is read from the ``DATABASE_URL`` environment variable so
that different environments (dev, staging, production) can point at different
PostgreSQL instances without code changes.

Connection pooling is handled by SQLAlchemy's built-in QueuePool:

* ``pool_size`` — number of persistent connections kept open (default: 5).
* ``max_overflow`` — extra connections allowed above pool_size under load (default: 10).
* ``pool_pre_ping`` — test each connection before use to discard stale ones.
* ``pool_recycle`` — recycle connections after 30 minutes to avoid server-side
  timeouts silently closing idle connections.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://beyond:beyond@localhost:5432/beyond",
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
