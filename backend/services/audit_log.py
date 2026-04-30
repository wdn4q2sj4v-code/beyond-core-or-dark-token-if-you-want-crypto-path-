"""
Audit log service for the BEYOND backend.

``create_audit_log`` is the single entry-point for recording audit events.
It persists an ``AuditLog`` row and returns the saved instance.  Callers
supply the actor, the action type, the target resource, optional before/after
state snapshots, and the originating HTTP request (used to capture the
client IP address and user-agent).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from models import AuditLog, User

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    *,
    actor: Optional[User],
    action_type: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    reason: Optional[str] = None,
    summary: Optional[str] = None,
    before: Optional[Any] = None,
    after: Optional[Any] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """Persist an audit log entry and return the saved instance.

    Args:
        db: Active SQLAlchemy session.
        actor: The ``User`` responsible for the action, or ``None`` for
            system-initiated events.
        action_type: A machine-readable identifier for the action, e.g.
            ``"governance_brain_release_gate_evaluated"``.
        target_type: The kind of resource being acted upon, e.g.
            ``"notification_rule_approval_request"``.
        target_id: String representation of the target's primary key.
        reason: Short, human-readable explanation of *why* the action was taken.
        summary: A concise, one-line description of the outcome.
        before: JSON-serialisable snapshot of the resource state *before* the
            action.  Pass ``None`` when no prior state exists (e.g. creation
            events).
        after: JSON-serialisable snapshot of the resource state *after* the
            action.
        request: The originating ``fastapi.Request``.  When supplied, the
            client IP address and ``User-Agent`` header are extracted and
            stored.

    Returns:
        The newly created and committed ``AuditLog`` instance.
    """
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    entry = AuditLog(
        actor_id=actor.id if actor is not None else None,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        summary=summary,
        before=before,
        after=after,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    logger.info(
        "Audit log created: action_type=%s target_type=%s target_id=%s actor_id=%s",
        action_type,
        target_type,
        target_id,
        entry.actor_id,
    )

    return entry
