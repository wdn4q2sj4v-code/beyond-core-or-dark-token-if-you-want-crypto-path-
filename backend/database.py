from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./beyond.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class GovernanceBrain(Base):
    """Stores the outcome of a single governance evaluation."""

    __tablename__ = "governance_brain"

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(String, nullable=False, index=True)
    decision = Column(String, nullable=False)
    governance_score = Column(Float, nullable=False)
    reasons_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)


class DualOverride(Base):
    """Represents a dual-superadmin override for a blocked approval request."""

    __tablename__ = "dual_override"

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(String, nullable=False, index=True)
    # "pending" → not yet consumed; "used" → already consumed
    status = Column(String, nullable=False, default="pending")
    approved_by_1 = Column(String, nullable=False)
    approved_by_2 = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)


def get_db():
    """FastAPI dependency that yields a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)


def init_db() -> None:
    """Create all database tables. Call this once at application startup."""
    Base.metadata.create_all(bind=engine)
