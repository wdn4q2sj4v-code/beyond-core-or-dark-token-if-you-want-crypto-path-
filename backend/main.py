from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import GovernanceOverrideRequest
from services import approve_governance_override

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.post("/governance/overrides/{override_id}/approve")
def approve_override(override_id: int, user_id: int, db: Session = Depends(get_db)):
    try:
        row = approve_governance_override(db, override_id=override_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": row.id,
        "status": row.status,
        "created_by_user_id": row.created_by_user_id,
        "first_approved_by_user_id": row.first_approved_by_user_id,
        "first_approved_at": row.first_approved_at,
        "second_approved_by_user_id": row.second_approved_by_user_id,
        "second_approved_at": row.second_approved_at,
    }
