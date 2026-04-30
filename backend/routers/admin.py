from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# In-memory store for governance override requests
_governance_overrides: List[Dict[str, Any]] = []


class GovernanceOverrideIn(BaseModel):
    policy: str
    reason: str
    requested_by: str


class GovernanceOverrideRow(BaseModel):
    id: str
    policy: str
    reason: str
    requested_by: str
    status: str
    created_at: datetime


def create_governance_override_request(payload: GovernanceOverrideIn) -> GovernanceOverrideRow:
    row = GovernanceOverrideRow(
        id=str(uuid4()),
        policy=payload.policy,
        reason=payload.reason,
        requested_by=payload.requested_by,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    _governance_overrides.append(row.model_dump())
    return row


@router.post("/admin/governance-overrides", response_model=GovernanceOverrideRow, status_code=201)
def create_override(payload: GovernanceOverrideIn):
    row = create_governance_override_request(payload)
    return row
