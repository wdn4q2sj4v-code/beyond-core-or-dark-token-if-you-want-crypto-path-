"""
Re-exports all SQLAlchemy models so Alembic env.py can import them with a
single wildcard import and have all metadata registered on Base.
"""

from app.models.approval_request import NotificationRuleApprovalRequest  # noqa: F401
from app.models.governance import GovernanceBrainDecision, ReleaseGateDecision  # noqa: F401
