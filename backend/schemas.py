from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GovernanceOverrideApproveRequest(BaseModel):
    approved_by: str


class GovernanceOverrideResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    approved_at: Optional[datetime]
    approved_by: Optional[str]

    model_config = {"from_attributes": True}
