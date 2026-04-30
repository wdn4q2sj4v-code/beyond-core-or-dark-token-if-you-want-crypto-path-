"""
Re-exports all SQLAlchemy models so that Alembic's env.py can import them
with a single wildcard import and have every model registered on Base.metadata.
"""

from app.models.approval_request import NotificationRuleApprovalRequest  # noqa: F401
from app.models.governance import GovernanceBrainDecision, ReleaseGateDecision  # noqa: F401
