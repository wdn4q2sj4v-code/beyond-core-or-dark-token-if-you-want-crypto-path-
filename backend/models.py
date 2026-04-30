import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum
from database import Base


class OverrideStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"


class GovernanceOverrideRequest(Base):
    __tablename__ = "governance_override_requests"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(OverrideStatus), nullable=False, default=OverrideStatus.pending)
    created_by_user_id = Column(Integer, nullable=False)
    first_approved_by_user_id = Column(Integer, nullable=True)
    first_approved_at = Column(DateTime(timezone=True), nullable=True)
    second_approved_by_user_id = Column(Integer, nullable=True)
    second_approved_at = Column(DateTime(timezone=True), nullable=True)
