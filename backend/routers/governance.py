"""
Governance router.

Exposes endpoints for governance-related operations:

* ``POST /governance/release-gate/{request_id}``
  Evaluates release eligibility of a notification rule approval request via
  the GovernanceBrain and records the decision in the audit log.

* ``POST /governance/approval-requests``
  Creates a new notification rule approval request (for testing / seeding).

* ``GET /governance/audit-logs``
  Returns recent audit log entries.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from audit import create_audit_log
from database import get_db
from models import AuditLog, NotificationRuleApprovalRequest
from schemas import (
    AuditLogRead,
    GovernanceDecisionResponse,
    NotificationRuleApprovalRequestCreate,
    NotificationRuleApprovalRequestRead,
)
from services.governance_brain import GovernanceBrain

router = APIRouter(prefix="/governance", tags=["governance"])


def _current_user(request: Request) -> str:
    """Return the authenticated user identity from request headers.

    In a production system this would validate a JWT / session token.
    For now the value is read from the ``X-User`` header with a fallback
    to ``"anonymous"``.
    """
    return request.headers.get("x-user", "anonymous")


@router.post(
    "/release-gate/{request_id}",
    response_model=GovernanceDecisionResponse,
    summary="Evaluate release gate for a notification rule approval request",
)
def evaluate_release_gate(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> GovernanceDecisionResponse:
    """Run the Governance Brain against the specified approval request and
    persist the decision as an audit log entry.

    Args:
        request_id: Primary key of the ``NotificationRuleApprovalRequest``.
        request: Incoming HTTP request (used for IP extraction and user identity).
        db: Injected SQLAlchemy session.

    Returns:
        A ``GovernanceDecisionResponse`` containing the brain's decision and
        score, plus a flag indicating that the audit log was created.

    Raises:
        HTTPException 404: When no approval request with ``request_id`` exists.
    """
    approval_request = (
        db.query(NotificationRuleApprovalRequest)
        .filter(NotificationRuleApprovalRequest.id == request_id)
        .first()
    )
    if approval_request is None:
        raise HTTPException(
            status_code=404,
            detail=f"NotificationRuleApprovalRequest {request_id} not found",
        )

    current_user = _current_user(request)

    brain = GovernanceBrain().evaluate(approval_request)

    create_audit_log(
        db=db,
        actor=current_user,
        action_type="governance_brain_release_gate_evaluated",
        target_type="notification_rule_approval_request",
        target_id=str(request_id),
        reason="Governance Brain evaluated release eligibility",
        summary=f"Governance decision: {brain.decision} score={brain.governance_score}",
        before=None,
        after={
            "decision": brain.decision,
            "governance_score": brain.governance_score,
            "signals": brain.signals_json,
            "reasons": brain.reasons_json,
        },
        request=request,
    )

    return GovernanceDecisionResponse(
        request_id=request_id,
        decision=brain.decision,
        governance_score=brain.governance_score,
        signals=brain.signals_json,
        reasons=brain.reasons_json,
        audit_log_created=True,
    )


@router.post(
    "/approval-requests",
    response_model=NotificationRuleApprovalRequestRead,
    status_code=201,
    summary="Create a notification rule approval request",
)
def create_approval_request(
    body: NotificationRuleApprovalRequestCreate,
    db: Session = Depends(get_db),
) -> NotificationRuleApprovalRequestRead:
    """Persist a new notification rule approval request.

    Args:
        body: Request payload.
        db: Injected SQLAlchemy session.

    Returns:
        The created ``NotificationRuleApprovalRequest``.
    """
    obj = NotificationRuleApprovalRequest(
        rule_name=body.rule_name,
        requested_by=body.requested_by,
        description=body.description,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/audit-logs",
    response_model=List[AuditLogRead],
    summary="List recent audit log entries",
)
def list_audit_logs(
    limit: int = 50,
    action_type: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[AuditLogRead]:
    """Return the most recent audit log entries, newest first.

    Args:
        limit: Maximum number of entries to return (default 50, max 200).
        action_type: Optional filter to return only entries of a specific type.
        db: Injected SQLAlchemy session.
    """
    limit = min(limit, 200)
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    return query.limit(limit).all()
