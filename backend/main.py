from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
from queries import find_valid_dual_override

# Create tables on startup (no-op if they already exist)
Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.get("/governance/override/{approval_request_id}")
def get_dual_override(approval_request_id: int, db: Session = Depends(get_db)):
    """Return the most recent valid dual-approved governance override for the
    given *approval_request_id*, or 404 if none exists."""
    record = find_valid_dual_override(db, approval_request_id=approval_request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No valid dual override found")
    return {
        "id": record.id,
        "approval_request_id": record.approval_request_id,
        "status": record.status,
        "first_approved_by_user_id": record.first_approved_by_user_id,
        "second_approved_by_user_id": record.second_approved_by_user_id,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
