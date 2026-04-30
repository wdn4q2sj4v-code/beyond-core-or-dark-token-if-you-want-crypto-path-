from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./beyond.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class ReleaseRequest(Base):
    __tablename__ = "release_requests"

    id = Column(Integer, primary_key=True, index=True)
    token_count = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")


Base.metadata.create_all(bind=engine)


class GovernanceBrain:
    """Evaluates a release request and produces a governance decision."""

    APPROVAL_THRESHOLD = 50

    def __init__(self, token_count: int) -> None:
        self.reasons: list[str] = []
        self.governance_score: int = 100

        if token_count <= 0:
            self.governance_score -= 60
            self.reasons.append("token_count must be greater than zero")

        if token_count > 10_000:
            self.governance_score -= 60
            self.reasons.append("token_count exceeds single-release limit of 10,000")

        self.decision = (
            "approved" if self.governance_score >= self.APPROVAL_THRESHOLD else "denied"
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


class ReleaseRequestIn(BaseModel):
    token_count: int


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.post("/release")
def release_tokens(payload: ReleaseRequestIn, db: Session = Depends(get_db)):
    brain = GovernanceBrain(token_count=payload.token_count)

    released_count = payload.token_count if brain.decision == "approved" else 0
    status = "released" if brain.decision == "approved" else "rejected"

    row = ReleaseRequest(token_count=payload.token_count, status=status)
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "request_id": row.id,
        "status": row.status,
        "released_count": released_count,
        "governance_decision": {
            "decision": brain.decision,
            "governance_score": brain.governance_score,
            "reasons": brain.reasons,
        },
    }

