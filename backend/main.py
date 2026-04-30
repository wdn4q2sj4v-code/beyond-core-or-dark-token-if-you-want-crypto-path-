import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
import uuid

app = FastAPI()

# ---------------------------------------------------------------------------
# In-memory store (v1)
# ---------------------------------------------------------------------------
_approvals: dict[str, dict] = {}

SUPERADMIN_TOKEN = os.environ.get("SUPERADMIN_TOKEN", "")
REQUIRED_APPROVALS = 2


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ApprovalRequest(BaseModel):
    title: str
    description: Optional[str] = None
    requester: str


class ApproveAction(BaseModel):
    approver: str

    @field_validator("approver")
    @classmethod
    def approver_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("approver must not be empty")
        return v.strip()


class SuperadminOverride(BaseModel):
    token: str
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason must not be empty")
        return v.strip()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.post("/approvals", status_code=201)
def create_approval(body: ApprovalRequest):
    """Create a new dual-approval request."""
    request_id = str(uuid.uuid4())
    _approvals[request_id] = {
        "id": request_id,
        "title": body.title,
        "description": body.description,
        "requester": body.requester,
        "approvers": [],
        "status": "pending",      # pending | approved | overridden
        "override_reason": None,
    }
    return _approvals[request_id]


@app.get("/approvals/{request_id}")
def get_approval(request_id: str):
    """Retrieve the current state of an approval request."""
    record = _approvals.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return record


@app.post("/approvals/{request_id}/approve")
def approve(request_id: str, body: ApproveAction):
    """Cast an approval.  Once REQUIRED_APPROVALS distinct approvers have
    approved, the request transitions to 'approved'."""
    record = _approvals.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if record["status"] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Request is already '{record['status']}' and cannot be approved again",
        )

    approver = body.approver  # already stripped/validated by Pydantic

    if approver == record["requester"]:
        raise HTTPException(status_code=409, detail="The requester cannot approve their own request")

    if approver in record["approvers"]:
        raise HTTPException(status_code=409, detail="This approver has already approved")

    record["approvers"].append(approver)

    if len(record["approvers"]) >= REQUIRED_APPROVALS:
        record["status"] = "approved"

    return record


@app.post("/approvals/{request_id}/superadmin-override")
def superadmin_override(request_id: str, body: SuperadminOverride):
    """Superadmin bypass: approves the request immediately, skipping the
    dual-approval requirement.  Requires the correct superadmin token."""
    if body.token != SUPERADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid superadmin token")

    record = _approvals.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if record["status"] == "approved":
        raise HTTPException(status_code=409, detail="Request is already approved")

    if record["status"] == "overridden":
        raise HTTPException(status_code=409, detail="Request has already been overridden")

    record["status"] = "overridden"
    record["override_reason"] = body.reason  # already stripped/validated by Pydantic
    return record
