from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class NotificationRuleApprovalRequestCreate(BaseModel):
    rule_name: str
    requested_by: str
    description: Optional[str] = None


class NotificationRuleApprovalRequestRead(BaseModel):
    id: int
    rule_name: str
    requested_by: str
    status: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GovernanceDecisionResponse(BaseModel):
    request_id: int
    decision: str
    governance_score: float
    signals: Dict[str, Any]
    reasons: List[str]
    audit_log_created: bool


class AuditLogRead(BaseModel):
    id: int
    actor: Optional[str] = None
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    reason: Optional[str] = None
    summary: Optional[str] = None
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
