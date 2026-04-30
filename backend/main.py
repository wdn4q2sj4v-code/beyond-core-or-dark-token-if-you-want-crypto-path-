from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime, timezone

app = FastAPI()


class OverrideStatus(str, Enum):
    pending = "pending"
    approved_first = "approved_first"
    approved = "approved"
    rejected = "rejected"


class GovernanceOverrideRequestCreate(BaseModel):
    brain_decision_id: str
    reason: str
    created_by: str


class ApproveRequest(BaseModel):
    approver: str


class GovernanceOverrideRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    request_id: str
    brain_decision_id: str
    status: OverrideStatus
    reason: str
    created_by: str
    first_approver: Optional[str] = None
    second_approver: Optional[str] = None
    created_at: datetime


_store: dict[str, GovernanceOverrideRequest] = {}


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.post("/governance-override-requests", response_model=GovernanceOverrideRequest, status_code=201)
def create_governance_override_request(body: GovernanceOverrideRequestCreate):
    request_id = str(uuid.uuid4())
    record = GovernanceOverrideRequest(
        request_id=request_id,
        brain_decision_id=body.brain_decision_id,
        status=OverrideStatus.pending,
        reason=body.reason,
        created_by=body.created_by,
        created_at=datetime.now(timezone.utc),
    )
    _store[request_id] = record
    return record


@app.get("/governance-override-requests", response_model=list[GovernanceOverrideRequest])
def list_governance_override_requests():
    return list(_store.values())


@app.get("/governance-override-requests/{request_id}", response_model=GovernanceOverrideRequest)
def get_governance_override_request(request_id: str):
    record = _store.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Governance override request not found")
    return record


@app.post("/governance-override-requests/{request_id}/approve", response_model=GovernanceOverrideRequest)
def approve_governance_override_request(request_id: str, body: ApproveRequest):
    record = _store.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Governance override request not found")
    if record.status == OverrideStatus.approved:
        raise HTTPException(status_code=400, detail="Request has already been fully approved")
    if record.status == OverrideStatus.rejected:
        raise HTTPException(status_code=400, detail="Request has been rejected and cannot be approved")
    if record.status == OverrideStatus.pending:
        record.first_approver = body.approver
        record.status = OverrideStatus.approved_first
    elif record.status == OverrideStatus.approved_first:
        if record.first_approver == body.approver:
            raise HTTPException(status_code=400, detail="Second approver must be different from the first approver")
        record.second_approver = body.approver
        record.status = OverrideStatus.approved
    return record
