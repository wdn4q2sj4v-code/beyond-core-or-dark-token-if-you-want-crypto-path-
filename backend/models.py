from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GovernanceOverrideApproveRequest(BaseModel):
    approved_by: str
    notes: Optional[str] = None


class GovernanceOverrideResponse(BaseModel):
    id: str
    status: str
    approved_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
