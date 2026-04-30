from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

GovernanceOverrideStatus = Literal["pending", "approved", "rejected", "used", "expired"]


class GovernanceOverrideRequestCreate(BaseModel):
    approval_request_id: int
    governance_brain_decision_id: int
    reason: str
    created_by_user_id: int


class GovernanceOverrideRequestUpdate(BaseModel):
    status: Optional[GovernanceOverrideStatus] = None
    first_approved_by_user_id: Optional[int] = None
    second_approved_by_user_id: Optional[int] = None
    first_approved_at: Optional[datetime] = None
    second_approved_at: Optional[datetime] = None
    used_at: Optional[datetime] = None


class GovernanceOverrideRequestRead(BaseModel):
    id: int
    approval_request_id: int
    governance_brain_decision_id: int
    status: GovernanceOverrideStatus
    reason: str
    created_by_user_id: int
    first_approved_by_user_id: Optional[int] = None
    second_approved_by_user_id: Optional[int] = None
    first_approved_at: Optional[datetime] = None
    second_approved_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
