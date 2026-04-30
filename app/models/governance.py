"""
SQLAlchemy models for governance brain decisions and release gate decisions.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean

from app.database import Base


class GovernanceBrainDecision(Base):
    """Stores the outcome of a governance brain evaluation for an approval request.

    The governance brain analyses signals attached to an approval request and
    produces a single decision string together with a numeric governance score
    and structured JSON containing the reasons and signals that drove the
    decision.
    """

    __tablename__ = "governance_brain_decisions"

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(
        Integer,
        ForeignKey("notification_rule_approval_requests.id"),
        nullable=False,
        index=True,
    )
    evaluated_by_user_id = Column(Integer, nullable=False)
    decision = Column(String, nullable=False)
    governance_score = Column(Float, nullable=False, default=0.0)
    reasons_json = Column(Text, nullable=True)
    signals_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<GovernanceBrainDecision id={self.id}"
            f" approval_request_id={self.approval_request_id}"
            f" decision={self.decision}>"
        )


class ReleaseGateDecision(Base):
    """Stores the persisted outcome of release-gate evaluation for an approval request.

    Each gate that was evaluated during a release attempt produces one row so
    that gate results are auditable after the fact.
    """

    __tablename__ = "release_gate_decisions"

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(
        Integer,
        ForeignKey("notification_rule_approval_requests.id"),
        nullable=False,
        index=True,
    )
    gate_name = Column(String, nullable=False)
    passed = Column(Boolean, nullable=False)
    details_json = Column(Text, nullable=True)
    evaluated_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ReleaseGateDecision id={self.id}"
            f" approval_request_id={self.approval_request_id}"
            f" gate_name={self.gate_name} passed={self.passed}>"
        )
