"""
Governance Brain decision service.

The Governance Brain analyses a set of signals attached to an approval request
and produces a structured decision that downstream code can use to determine
whether a release should proceed.

Supported decisions
-------------------
``auto_promote``
    All signals are positive and the governance score is high enough that the
    release can proceed without additional human review.

``approve_with_review``
    Some signals are mixed but overall the request is approvable, subject to a
    human reviewer signing off.

``hold_for_review``
    Signals indicate a higher risk situation; the release should be paused until
    a reviewer explicitly clears it.

``reject``
    One or more hard-blocking signals were found; the release must not proceed.

Public API
----------
create_governance_brain_decision(db, *, approval_request_id, user_id) -> GovernanceBrainDecision
    Evaluate signals and persist + return a new ``GovernanceBrainDecision`` row.
"""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.governance import GovernanceBrainDecision
from app.models.approval_request import NotificationRuleApprovalRequest


# ---------------------------------------------------------------------------
# Signal evaluators
# ---------------------------------------------------------------------------

def _signal_approval_age_hours(row: NotificationRuleApprovalRequest) -> dict:
    """Measure how long the request has been in approved state.

    Requests approved very recently (< 1 hour) receive a slight risk signal
    to encourage a cooling-off period.
    """
    age_seconds = (datetime.now(timezone.utc) - row.updated_at.replace(tzinfo=timezone.utc)).total_seconds()
    age_hours = age_seconds / 3600
    if age_hours < 1:
        return {
            "name": "approval_age",
            "value": age_hours,
            "risk": "medium",
            "note": "Request was approved less than 1 hour ago.",
        }
    return {
        "name": "approval_age",
        "value": age_hours,
        "risk": "low",
        "note": f"Request has been approved for {age_hours:.1f} hours.",
    }


def _signal_requester_known(row: NotificationRuleApprovalRequest) -> dict:
    """Check whether the requesting user is a known/trusted identity.

    This is a placeholder that always marks the requester as known.  Replace
    with a real lookup against your user trust store when available.
    """
    return {
        "name": "requester_known",
        "value": row.requested_by_user_id,
        "risk": "low",
        "note": "Requester identity is on record.",
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

_RISK_WEIGHTS = {"low": 1.0, "medium": 0.6, "high": 0.2, "critical": 0.0}


def _compute_governance_score(signals: list[dict]) -> float:
    """Return a score in [0, 1] based on the risk levels of *signals*.

    A score of 1.0 means all signals are low risk; a score of 0.0 means at
    least one signal is critical.
    """
    if not signals:
        return 1.0
    weights = [_RISK_WEIGHTS.get(s.get("risk", "low"), 1.0) for s in signals]
    return sum(weights) / len(weights)


def _decide(governance_score: float, signals: list[dict]) -> tuple[str, list[str]]:
    """Derive a decision string and list of human-readable reasons from the score."""
    reasons: list[str] = [s["note"] for s in signals]

    has_critical = any(s.get("risk") == "critical" for s in signals)
    has_high = any(s.get("risk") == "high" for s in signals)

    if has_critical:
        return "reject", reasons
    if has_high or governance_score < 0.4:
        return "hold_for_review", reasons
    if governance_score < 0.75:
        return "approve_with_review", reasons
    return "auto_promote", reasons


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_governance_brain_decision(
    db: Session,
    *,
    approval_request_id: int,
    user_id: int,
) -> GovernanceBrainDecision:
    """Evaluate governance signals and persist a new decision row.

    Args:
        db: Active SQLAlchemy session.
        approval_request_id: Primary key of the approval request to evaluate.
        user_id: Primary key of the user triggering the evaluation.

    Returns:
        The newly created and committed ``GovernanceBrainDecision`` instance.

    Raises:
        ValueError: If the approval request does not exist.
    """
    row = (
        db.query(NotificationRuleApprovalRequest)
        .filter(NotificationRuleApprovalRequest.id == approval_request_id)
        .first()
    )
    if row is None:
        raise ValueError(
            f"Approval request {approval_request_id} not found."
        )

    signals = [
        _signal_approval_age_hours(row),
        _signal_requester_known(row),
    ]

    governance_score = _compute_governance_score(signals)
    decision, reasons = _decide(governance_score, signals)

    record = GovernanceBrainDecision(
        approval_request_id=approval_request_id,
        evaluated_by_user_id=user_id,
        decision=decision,
        governance_score=governance_score,
        reasons_json=json.dumps(reasons),
        signals_json=json.dumps(signals),
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
