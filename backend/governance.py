"""
Governance enforcement logic.

Core rule
---------
If the brain's decision is not in the set of allowed decisions, a valid
dual-superadmin override must exist for the given approval request.  If one
does, it is consumed (status → "used").  If none exists the release is blocked
and a ValueError is raised.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database import DualOverride, GovernanceBrain

# Decisions that allow a release to proceed without an override.
ALLOWED_DECISIONS: frozenset[str] = frozenset({"approved", "conditionally_approved"})


def find_valid_dual_override(
    db: Session,
    *,
    approval_request_id: str,
) -> Optional[DualOverride]:
    """Return the first unused dual-override for *approval_request_id*, or None."""
    return (
        db.query(DualOverride)
        .filter(
            DualOverride.approval_request_id == approval_request_id,
            DualOverride.status == "pending",
        )
        .first()
    )


def enforce_governance_decision(
    db: Session,
    *,
    brain: GovernanceBrain,
    request_id: str,
    allowed_decisions: frozenset[str] = ALLOWED_DECISIONS,
) -> None:
    """
    Enforce the governance-brain decision for *request_id*.

    Raises
    ------
    ValueError
        When the brain's decision is blocked and no valid dual override exists.
    """
    if brain.decision not in allowed_decisions:
        override = find_valid_dual_override(db, approval_request_id=request_id)

        if not override:
            raise ValueError(
                {
                    "message": (
                        "Release blocked by Governance Brain. "
                        "Dual superadmin override required."
                    ),
                    "governance_decision": {
                        "decision": brain.decision,
                        "score": brain.governance_score,
                        "reasons": brain.reasons_json,
                    },
                }
            )

        override.status = "used"
        override.used_at = datetime.utcnow()
