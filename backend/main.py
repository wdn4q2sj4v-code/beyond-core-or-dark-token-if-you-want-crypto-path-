import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import DualOverride, GovernanceBrain, get_db, init_db
from governance import ALLOWED_DECISIONS, enforce_governance_decision


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="BEYOND Governance API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ApprovalRequest(BaseModel):
    request_id: str
    decision: str
    governance_score: float
    reasons: list[str] = []


class OverrideRequest(BaseModel):
    approval_request_id: str
    approved_by_1: str
    approved_by_2: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.post("/governance/evaluate")
def evaluate_governance(payload: ApprovalRequest, db: Session = Depends(get_db)):
    """
    Evaluate a governance decision for an approval request.

    - If the decision is in the allowed set the request is approved immediately.
    - If it is blocked, a pending dual-superadmin override is consumed when present;
      otherwise a 403 error is returned with the governance details.
    """
    brain = GovernanceBrain(
        approval_request_id=payload.request_id,
        decision=payload.decision,
        governance_score=payload.governance_score,
        reasons_json=json.dumps(payload.reasons),
    )
    db.add(brain)

    try:
        enforce_governance_decision(
            db,
            brain=brain,
            request_id=payload.request_id,
            allowed_decisions=ALLOWED_DECISIONS,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=exc.args[0]) from exc

    db.commit()
    return {"status": "approved", "request_id": payload.request_id}


@app.post("/governance/override")
def create_override(payload: OverrideRequest, db: Session = Depends(get_db)):
    """Register a dual-superadmin override for a blocked approval request."""
    override = DualOverride(
        approval_request_id=payload.approval_request_id,
        approved_by_1=payload.approved_by_1,
        approved_by_2=payload.approved_by_2,
        status="pending",
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return {"status": "override_created", "override_id": override.id}
