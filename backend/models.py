from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class GovernanceOverrideRequest(Base):
    __tablename__ = "governance_override_requests"

    id = Column(Integer, primary_key=True, index=True)

    approval_request_id = Column(Integer, nullable=False, index=True)
    governance_brain_decision_id = Column(Integer, nullable=False, index=True)

    status = Column(String(30), nullable=False, default="pending")
    # pending / approved / rejected / used / expired

    reason = Column(Text, nullable=False)

    created_by_user_id = Column(Integer, nullable=False, index=True)
    first_approved_by_user_id = Column(Integer, nullable=True, index=True)
    second_approved_by_user_id = Column(Integer, nullable=True, index=True)

    first_approved_at = Column(DateTime, nullable=True)
    second_approved_at = Column(DateTime, nullable=True)
    used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
