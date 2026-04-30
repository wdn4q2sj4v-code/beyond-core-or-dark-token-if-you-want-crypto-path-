"""
Release gate evaluation and persistence for notification rule approval requests.

A *release gate* is a policy check that must pass before an approved request
can be released to production.  Gates are evaluated as a group: all gates run
regardless of whether an earlier gate has already failed, so that callers get a
complete picture of what needs to be fixed.

Public API
----------
evaluate_release_gates(db, request_id) -> dict
    Run all gates for the given request and return a summary dict that includes
    a ``release_allowed`` boolean and per-gate results.

persist_gate_decisions(db, request_id, gate_result, *, evaluated_by_user_id) -> None
    Write each gate outcome from a previous ``evaluate_release_gates`` call to
    the ``release_gate_decisions`` table.
"""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.approval_request import NotificationRuleApprovalRequest
from app.models.governance import ReleaseGateDecision


# ---------------------------------------------------------------------------
# Internal gate implementations
# ---------------------------------------------------------------------------

def _gate_request_exists(db: Session, request_id: int) -> dict:
    """Verify that the approval request row still exists and is in an approved state."""
    row = (
        db.query(NotificationRuleApprovalRequest)
        .filter(NotificationRuleApprovalRequest.id == request_id)
        .first()
    )
    if row is None:
        return {"passed": False, "details": "Approval request not found."}
    if row.status != "approved":
        return {
            "passed": False,
            "details": f"Request status is '{row.status}', expected 'approved'.",
        }
    return {"passed": True, "details": "Request exists and is approved."}


def _gate_no_open_blockers(db: Session, request_id: int) -> dict:
    """Check that no open blocker issues are associated with this request.

    This is a placeholder implementation.  Replace the body with a real query
    against your blocker/issue table once that model exists.
    """
    # No blocker table exists yet — gate passes by default.
    return {"passed": True, "details": "No open blockers detected."}


def _gate_governance_score_threshold(db: Session, request_id: int) -> dict:
    """Verify that no prior governance brain decision recorded a critically low score.

    Decisions with a governance_score below 0.2 are treated as blocking.
    """
    from app.models.governance import GovernanceBrainDecision  # avoid circular import

    latest = (
        db.query(GovernanceBrainDecision)
        .filter(GovernanceBrainDecision.approval_request_id == request_id)
        .order_by(GovernanceBrainDecision.created_at.desc())
        .first()
    )
    if latest is None:
        # No prior decision recorded — gate passes (governance brain will run later).
        return {"passed": True, "details": "No prior governance score to evaluate."}
    if latest.governance_score < 0.2:
        return {
            "passed": False,
            "details": (
                f"Governance score {latest.governance_score:.2f} is below the"
                " minimum threshold of 0.20."
            ),
        }
    return {
        "passed": True,
        "details": f"Governance score {latest.governance_score:.2f} meets threshold.",
    }


# ---------------------------------------------------------------------------
# Ordered list of (gate_name, gate_fn) pairs
# ---------------------------------------------------------------------------

_GATES = [
    ("request_exists", _gate_request_exists),
    ("no_open_blockers", _gate_no_open_blockers),
    ("governance_score_threshold", _gate_governance_score_threshold),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_release_gates(db: Session, request_id: int) -> dict:
    """Run all release gates for *request_id* and return a summary.

    Args:
        db: Active SQLAlchemy session.
        request_id: Primary key of the ``NotificationRuleApprovalRequest`` to
            evaluate.

    Returns:
        A dict with the following keys:

        ``release_allowed`` (bool)
            ``True`` if every gate passed; ``False`` otherwise.

        ``gates`` (dict[str, dict])
            Per-gate results.  Each value has keys ``passed`` (bool) and
            ``details`` (str).
    """
    results: dict[str, dict] = {}
    all_passed = True

    for gate_name, gate_fn in _GATES:
        outcome = gate_fn(db, request_id)
        results[gate_name] = outcome
        if not outcome["passed"]:
            all_passed = False

    return {"release_allowed": all_passed, "gates": results}


def persist_gate_decisions(
    db: Session,
    request_id: int,
    gate_result: dict,
    *,
    evaluated_by_user_id: int,
) -> None:
    """Persist each gate outcome from *gate_result* to the database.

    Existing gate decisions for the same request are not deleted; each call
    appends a new set of rows so that the full history of gate evaluations is
    retained.

    Args:
        db: Active SQLAlchemy session.
        request_id: Primary key of the approval request that was evaluated.
        gate_result: The dict returned by ``evaluate_release_gates``.
        evaluated_by_user_id: Primary key of the user who triggered the release
            attempt.
    """
    now = datetime.now(timezone.utc)
    for gate_name, outcome in gate_result.get("gates", {}).items():
        row = ReleaseGateDecision(
            approval_request_id=request_id,
            gate_name=gate_name,
            passed=1 if outcome["passed"] else 0,
            details_json=json.dumps({"details": outcome.get("details")}),
            evaluated_by_user_id=evaluated_by_user_id,
            created_at=now,
        )
        db.add(row)
    db.commit()
