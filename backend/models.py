"""
SQLAlchemy models for the BEYOND backend.

Defines:
- ``User`` – authenticated users / actors in the system.
- ``NotificationRuleApprovalRequest`` – a request for a notification rule to be
  approved before a release.
- ``AuditLog`` – an immutable record of every significant action taken, including
  Governance Brain release-gate evaluations.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Float
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """An authenticated participant in the BEYOND system."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True)
    role = Column(String, default="member", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    audit_logs = relationship("AuditLog", back_populates="actor", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username}>"


class NotificationRuleApprovalRequest(Base):
    """A request for a notification rule to be approved before a release."""

    __tablename__ = "notification_rule_approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    requester = relationship("User", foreign_keys=[requester_id])

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<NotificationRuleApprovalRequest id={self.id}"
            f" rule_name={self.rule_name} status={self.status}>"
        )


class AuditLog(Base):
    """An immutable record of a significant action within the BEYOND system.

    Each row captures *who* did *what* to *which* resource, together with
    optional ``before`` / ``after`` snapshots of the affected state and the
    HTTP request context (IP address, user-agent).
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_type = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=True, index=True)
    target_id = Column(String, nullable=True, index=True)
    reason = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    actor = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog id={self.id} action_type={self.action_type}"
            f" target_type={self.target_type} target_id={self.target_id}>"
        )
