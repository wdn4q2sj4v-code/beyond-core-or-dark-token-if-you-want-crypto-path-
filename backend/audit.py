"""
Audit log helper.

Provides a single ``create_audit_log`` function that persists an immutable
audit trail entry to the database.  All fields except ``db``, ``action_type``
are optional so the function can be called uniformly across different contexts.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from models import AuditLog


def create_audit_log(
    db: Session,
    *,
    actor: Optional[str] = None,
    action_type: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    reason: Optional[str] = None,
    summary: Optional[str] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """Persist an audit log entry and return it.

    Args:
        db: Active SQLAlchemy session.
        actor: Identity of the user or system performing the action.
        action_type: Machine-readable action identifier
            (e.g. ``"governance_brain_release_gate_evaluated"``).
        target_type: Kind of object being acted upon
            (e.g. ``"notification_rule_approval_request"``).
        target_id: Primary key or other identifier of the target object.
        reason: Short human-readable explanation for the action.
        summary: Longer free-text summary, may include computed values.
        before: Snapshot of the affected object *before* the action.
        after: Snapshot of the affected object *after* the action.
        request: Optional FastAPI ``Request`` object; used to extract the
            originating IP address.

    Returns:
        The newly created and persisted ``AuditLog`` instance.
    """
    ip_address: Optional[str] = None
    if request is not None:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        elif request.client is not None:
            ip_address = request.client.host

    entry = AuditLog(
        actor=actor,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        summary=summary,
        before=before,
        after=after,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
