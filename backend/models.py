from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Decision(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    OVERRIDDEN = "OVERRIDDEN"


class ApprovalRequest(BaseModel):
    request_id: str = Field(..., description="Unique identifier for this request")
    requester: str = Field(..., description="Identity of the requester")
    action: str = Field(..., description="The action or release being requested")
    payload: dict = Field(default_factory=dict, description="Arbitrary metadata for the request")


class GovernanceDecision(BaseModel):
    request_id: str
    decision: Decision
    reasons: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OverrideRequest(BaseModel):
    request_id: str = Field(..., description="ID of the previously blocked request")
    superadmin: str = Field(..., description="Identity of the superadmin issuing the override")
    justification: str = Field(..., description="Reason for overriding the block")


class AuditEntry(BaseModel):
    event: str
    request_id: str
    actor: str
    detail: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
