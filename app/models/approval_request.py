"""
SQLAlchemy model for notification rule approval requests.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.database import Base


class NotificationRuleApprovalRequest(Base):
    """Represents an approval request for a notification rule change.

    Tracks the lifecycle of a change request from submission through
    approval/rejection and final release.
    """

    __tablename__ = "notification_rule_approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False, index=True)
    requested_by_user_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<NotificationRuleApprovalRequest id={self.id}"
            f" rule_id={self.rule_id} status={self.status}>"
        )
