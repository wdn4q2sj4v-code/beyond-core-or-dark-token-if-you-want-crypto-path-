"""
BEYOND backend – FastAPI application entry-point.

Endpoints
---------
GET  /
    Health-check.

POST /users/
    Create a new user (minimal fixture for development / testing).

POST /approval-requests/
    Create a notification rule approval request.

POST /governance/evaluate-release/{request_id}
    Run the Governance Brain against the specified approval request,
    write an audit log entry and return the evaluation result.

GET  /audit-logs/
    List audit log entries (supports optional ``action_type`` filter).
"""

import logging

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
from services.audit_log import create_audit_log
from services.governance_brain import GovernanceBrain

logging.basicConfig(level=logging.INFO)

# Create all tables on startup (sufficient for SQLite dev environments; use
# Alembic migrations for production).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BEYOND", version="1.0.0")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    username: str
    email: str | None = None
    role: str = "member"


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    role: str

    model_config = {"from_attributes": True}


class ApprovalRequestCreate(BaseModel):
    rule_name: str
    description: str | None = None
    requester_id: int | None = None


class ApprovalRequestOut(BaseModel):
    id: int
    rule_name: str
    description: str | None
    requester_id: int | None
    status: str

    model_config = {"from_attributes": True}


class GovernanceEvaluationOut(BaseModel):
    request_id: int
    decision: str
    governance_score: float
    signals: dict
    reasons: list[str]
    audit_log_id: int


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None
    action_type: str
    target_type: str | None
    target_id: str | None
    reason: str | None
    summary: str | None
    before: object
    after: object
    ip_address: str | None
    user_agent: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new user record."""
    existing = db.query(models.User).filter(models.User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' is already taken.",
        )
    user = models.User(username=payload.username, email=payload.email, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post(
    "/approval-requests/",
    response_model=ApprovalRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def create_approval_request(
    payload: ApprovalRequestCreate,
    db: Session = Depends(get_db),
):
    """Create a notification rule approval request."""
    if payload.requester_id is not None:
        requester = db.get(models.User, payload.requester_id)
        if requester is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {payload.requester_id} not found.",
            )
    approval_request = models.NotificationRuleApprovalRequest(
        rule_name=payload.rule_name,
        description=payload.description,
        requester_id=payload.requester_id,
        status="pending",
    )
    db.add(approval_request)
    db.commit()
    db.refresh(approval_request)
    return approval_request


@app.post(
    "/governance/evaluate-release/{request_id}",
    response_model=GovernanceEvaluationOut,
)
def evaluate_release_gate(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: int | None = None,
):
    """Run the Governance Brain release-gate evaluation for an approval request.

    The caller may pass ``current_user_id`` as a query parameter to associate
    the evaluation with a specific user.  When omitted the action is recorded
    as a system-level event (``actor=None``).
    """
    approval_request = db.get(models.NotificationRuleApprovalRequest, request_id)
    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request {request_id} not found.",
        )

    current_user: models.User | None = None
    if current_user_id is not None:
        current_user = db.get(models.User, current_user_id)
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {current_user_id} not found.",
            )

    brain = GovernanceBrain.evaluate(db, approval_request)

    audit_entry = create_audit_log(
        db=db,
        actor=current_user,
        action_type="governance_brain_release_gate_evaluated",
        target_type="notification_rule_approval_request",
        target_id=str(request_id),
        reason="Governance Brain evaluated release eligibility",
        summary=f"Governance decision: {brain.decision} score={brain.governance_score}",
        before=None,
        after={
            "decision": brain.decision,
            "governance_score": brain.governance_score,
            "signals": brain.signals_json,
            "reasons": brain.reasons_json,
        },
        request=request,
    )

    return GovernanceEvaluationOut(
        request_id=request_id,
        decision=brain.decision,
        governance_score=brain.governance_score,
        signals=brain.signals,
        reasons=brain.reasons,
        audit_log_id=audit_entry.id,
    )


@app.get("/audit-logs/", response_model=list[AuditLogOut])
def list_audit_logs(
    action_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return audit log entries, optionally filtered by ``action_type``."""
    query = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc())
    if action_type:
        query = query.filter(models.AuditLog.action_type == action_type)
    return query.limit(limit).all()

