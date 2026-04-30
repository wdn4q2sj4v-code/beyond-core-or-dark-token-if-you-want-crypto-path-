from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func

from database import Base


class NotificationRuleApprovalRequest(Base):
    """Represents a request for approval to release a notification rule."""

    __tablename__ = "notification_rule_approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String, nullable=False)
    requested_by = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<NotificationRuleApprovalRequest id={self.id}"
            f" rule_name={self.rule_name} status={self.status}>"
        )


class AuditLog(Base):
    """Immutable audit trail entry for governed actions in the system."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String, nullable=True)
    action_type = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=True, index=True)
    target_id = Column(String, nullable=True, index=True)
    reason = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog id={self.id} action_type={self.action_type}"
            f" target_type={self.target_type} target_id={self.target_id}>"
        )
