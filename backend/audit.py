"""In-memory audit log.

Every significant event (request received, decision made, override applied) is
appended here.  In production this would write to a persistent store.
"""
from __future__ import annotations

from typing import List

from models import AuditEntry

_audit_log: List[AuditEntry] = []


def record(event: str, request_id: str, actor: str, detail: str) -> AuditEntry:
    """Create and store an audit entry, then return it."""
    entry = AuditEntry(
        event=event,
        request_id=request_id,
        actor=actor,
        detail=detail,
    )
    _audit_log.append(entry)
    return entry


def get_all() -> List[AuditEntry]:
    """Return a copy of the full audit log."""
    return list(_audit_log)
