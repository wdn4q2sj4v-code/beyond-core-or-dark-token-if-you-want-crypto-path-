from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GovernanceOverrideCreate(BaseModel):
    target_policy: str
    override_value: str
    reason: str
    requested_by: str


class GovernanceOverrideRow(BaseModel):
    id: int
    target_policy: str
    override_value: str
    reason: str
    requested_by: str
    created_at: datetime
    status: str = "pending"
