from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import crud
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


class GovernanceOverrideRequestCreate(BaseModel):
    approval_request_id: int
    governance_brain_decision_id: int
    reason: str
    user_id: int


class GovernanceOverrideRequestResponse(BaseModel):
    id: int
    approval_request_id: int
    governance_brain_decision_id: int
    reason: str
    created_by_user_id: int
    status: str

    model_config = {"from_attributes": True}


@app.post("/governance/override-requests", status_code=201, response_model=GovernanceOverrideRequestResponse)
def create_override_request(
    payload: GovernanceOverrideRequestCreate,
    db: Session = Depends(get_db),
):
    try:
        record = crud.create_governance_override_request(
            db,
            approval_request_id=payload.approval_request_id,
            governance_brain_decision_id=payload.governance_brain_decision_id,
            reason=payload.reason,
            user_id=payload.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return record
