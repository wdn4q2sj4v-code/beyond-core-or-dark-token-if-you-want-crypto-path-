from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base


class GovernanceOverrideRequest(Base):
    __tablename__ = "governance_override_requests"

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
    first_approved_by_user_id = Column(Integer, nullable=True)
    second_approved_by_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
