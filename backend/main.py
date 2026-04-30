from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from enum import Enum

app = FastAPI()


# ── Enums ────────────────────────────────────────────────────────────────────

class OverrideStatus(str, Enum):
    pending = "pending"
    partially_approved = "partially_approved"
    approved = "approved"
    rejected = "rejected"


# ── Pydantic models ───────────────────────────────────────────────────────────

class GovernanceOverrideRequestCreate(BaseModel):
    brain_decision_id: str
    reason: str
    created_by: str


class GovernanceOverrideRequest(BaseModel):
    request_id: str
    brain_decision_id: str
    status: OverrideStatus
    reason: str
    created_by: str
    first_approver: Optional[str] = None
    second_approver: Optional[str] = None


class ApproveRequest(BaseModel):
    approver: str


# ── In-memory store ───────────────────────────────────────────────────────────

_override_requests: dict[str, GovernanceOverrideRequest] = {}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.post("/governance-override-requests", response_model=GovernanceOverrideRequest, status_code=201)
def create_override_request(body: GovernanceOverrideRequestCreate):
    """Create a new Governance Override Request."""
    request_id = str(uuid4())
    override = GovernanceOverrideRequest(
        request_id=request_id,
        brain_decision_id=body.brain_decision_id,
        status=OverrideStatus.pending,
        reason=body.reason,
        created_by=body.created_by,
    )
    _override_requests[request_id] = override
    return override


@app.get("/governance-override-requests", response_model=list[GovernanceOverrideRequest])
def list_override_requests():
    """List all Governance Override Requests."""
    return list(_override_requests.values())


@app.get("/governance-override-requests/{request_id}", response_model=GovernanceOverrideRequest)
def get_override_request(request_id: str):
    """Get a single Governance Override Request by ID."""
    override = _override_requests.get(request_id)
    if not override:
        raise HTTPException(status_code=404, detail="Override request not found")
    return override


@app.post("/governance-override-requests/{request_id}/approve", response_model=GovernanceOverrideRequest)
def approve_override_request(request_id: str, body: ApproveRequest):
    """Approve a Governance Override Request.

    The first call sets the first approver and moves status to
    ``partially_approved``.  The second call (by a different approver) sets the
    second approver and moves status to ``approved``.
    """
    override = _override_requests.get(request_id)
    if not override:
        raise HTTPException(status_code=404, detail="Override request not found")
    if override.status == OverrideStatus.approved:
        raise HTTPException(status_code=400, detail="Override request is already approved")
    if override.status == OverrideStatus.rejected:
        raise HTTPException(status_code=400, detail="Override request has been rejected and cannot be approved")
    if body.approver == override.created_by:
        raise HTTPException(status_code=400, detail="The request creator cannot approve their own override request")
    if override.first_approver is None:
        override.first_approver = body.approver
        override.status = OverrideStatus.partially_approved
    elif override.second_approver is None:
        if override.first_approver == body.approver:
            raise HTTPException(status_code=400, detail="Second approver must be different from the first approver")
        override.second_approver = body.approver
        override.status = OverrideStatus.approved
    return override
