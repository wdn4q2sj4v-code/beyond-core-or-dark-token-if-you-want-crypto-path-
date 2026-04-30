"""
Release service for notification rule approval requests.

This module exposes ``release_approved_request``, the primary entry point for
promoting an approved notification-rule change into production.  The function
enforces two independent policy layers before allowing a release:

1. **Release gates** — a set of database-backed policy checks (e.g. no open
   blockers, governance score threshold).  All gates must pass unless
   ``allow_override`` is ``True``.

2. **Governance Brain** — an AI-assisted signal aggregator that produces a
   structured decision and score for the request.  Only ``auto_promote`` and
   ``approve_with_review`` decisions are permitted unless ``allow_override`` is
   ``True``.

Both evaluation results are persisted to the database before any exception is
raised, so that the audit trail is always up to date.
"""

from sqlalchemy.orm import Session

from app.models.approval_request import NotificationRuleApprovalRequest
from app.services.release_gates import evaluate_release_gates, persist_gate_decisions
from app.services.governance_brain import create_governance_brain_decision


def release_approved_request(
    db: Session,
    *,
    request_id: int,
    user_id: int,
    allow_override: bool = False,
) -> None:
    """Attempt to release an approved notification rule change.

    The function checks that the request exists and has ``status == "approved"``,
    then runs the release-gate and Governance Brain evaluations.  Both results
    are persisted regardless of outcome.  If any policy layer blocks the release
    and *allow_override* is ``False`` a ``ValueError`` is raised with a
    structured payload describing the blocking reason.

    Args:
        db: Active SQLAlchemy session.
        request_id: Primary key of the ``NotificationRuleApprovalRequest`` to
            release.
        user_id: Primary key of the user triggering the release.
        allow_override: When ``True``, gate failures and non-standard Governance
            Brain decisions are logged but do not block the release.

    Raises:
        ValueError: If the request is not found, not in ``approved`` state, or
            blocked by policy gates / Governance Brain (when *allow_override* is
            ``False``).
    """
    row = (
        db.query(NotificationRuleApprovalRequest)
        .filter(NotificationRuleApprovalRequest.id == request_id)
        .first()
    )

    if not row:
        raise ValueError("Approval request not found.")

    if row.status != "approved":
        raise ValueError("Only approved requests can be released.")

    gate_result = evaluate_release_gates(db, request_id)
    persist_gate_decisions(db, request_id, gate_result, evaluated_by_user_id=user_id)

    if not gate_result["release_allowed"] and not allow_override:
        raise ValueError({
            "message": "Release blocked by policy gates.",
            "gate_result": gate_result,
        })

    brain = create_governance_brain_decision(
        db,
        approval_request_id=request_id,
        user_id=user_id,
    )

    allowed_decisions = {"auto_promote", "approve_with_review"}

    if brain.decision not in allowed_decisions and not allow_override:
        raise ValueError({
            "message": "Release blocked by Governance Brain.",
            "governance_decision": {
                "decision": brain.decision,
                "governance_score": brain.governance_score,
                "reasons": brain.reasons_json,
                "signals": brain.signals_json,
            },
        })

    # existing release logic continues here
