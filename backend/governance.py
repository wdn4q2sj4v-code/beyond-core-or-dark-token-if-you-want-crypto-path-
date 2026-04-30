from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class GovernanceOverrideStatus(str, Enum):
    governance_override_requested = "governance_override_requested"
    governance_override_first_approved = "governance_override_first_approved"
    governance_override_second_approved = "governance_override_second_approved"
    governance_override_used_for_release = "governance_override_used_for_release"
    governance_override_rejected = "governance_override_rejected"


# Which transitions are legal from a given status
_VALID_TRANSITIONS: Dict[GovernanceOverrideStatus, List[GovernanceOverrideStatus]] = {
    GovernanceOverrideStatus.governance_override_requested: [
        GovernanceOverrideStatus.governance_override_first_approved,
        GovernanceOverrideStatus.governance_override_rejected,
    ],
    GovernanceOverrideStatus.governance_override_first_approved: [
        GovernanceOverrideStatus.governance_override_second_approved,
        GovernanceOverrideStatus.governance_override_rejected,
    ],
    GovernanceOverrideStatus.governance_override_second_approved: [
        GovernanceOverrideStatus.governance_override_used_for_release,
        GovernanceOverrideStatus.governance_override_rejected,
    ],
    # Terminal states – no further transitions allowed
    GovernanceOverrideStatus.governance_override_used_for_release: [],
    GovernanceOverrideStatus.governance_override_rejected: [],
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class GovernanceOverrideRecord(BaseModel):
    id: str
    reason: str
    status: GovernanceOverrideStatus
    created_at: str
    updated_at: str
    history: List[str]


class CreateOverrideRequest(BaseModel):
    reason: str


class ApproveOverrideRequest(BaseModel):
    approver: str


class RejectOverrideRequest(BaseModel):
    rejector: str
    reason: Optional[str] = None


class UseForReleaseRequest(BaseModel):
    release_tag: str


# ---------------------------------------------------------------------------
# In-memory store (for demonstration only; replace with persistent storage in production)
# ---------------------------------------------------------------------------

_store: Dict[str, GovernanceOverrideRecord] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_or_404(override_id: str) -> GovernanceOverrideRecord:
    record = _store.get(override_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Override '{override_id}' not found")
    return record


def _transition(
    override_id: str,
    target: GovernanceOverrideStatus,
    history_entry: str,
) -> GovernanceOverrideRecord:
    record = _get_or_404(override_id)
    allowed = _VALID_TRANSITIONS[record.status]
    if target not in allowed:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot transition from '{record.status}' to '{target}'. "
                f"Allowed transitions: {[s.value for s in allowed] or 'none (terminal state)'}"
            ),
        )
    record.status = target
    record.updated_at = _now()
    record.history.append(history_entry)
    return record


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/governance/override", tags=["governance"])


@router.post("", response_model=GovernanceOverrideRecord, status_code=201)
def request_override(body: CreateOverrideRequest) -> GovernanceOverrideRecord:
    """Create a new governance override request."""
    now = _now()
    record = GovernanceOverrideRecord(
        id=str(uuid.uuid4()),
        reason=body.reason,
        status=GovernanceOverrideStatus.governance_override_requested,
        created_at=now,
        updated_at=now,
        history=[f"{now} — governance_override_requested: {body.reason}"],
    )
    _store[record.id] = record
    return record


@router.get("", response_model=List[GovernanceOverrideRecord])
def list_overrides() -> List[GovernanceOverrideRecord]:
    """List all governance override records."""
    return list(_store.values())


@router.get("/{override_id}", response_model=GovernanceOverrideRecord)
def get_override(override_id: str) -> GovernanceOverrideRecord:
    """Get a specific governance override record."""
    return _get_or_404(override_id)


@router.post("/{override_id}/approve", response_model=GovernanceOverrideRecord)
def approve_override(override_id: str, body: ApproveOverrideRequest) -> GovernanceOverrideRecord:
    """Approve a governance override (first or second approval)."""
    record = _get_or_404(override_id)

    if record.status == GovernanceOverrideStatus.governance_override_requested:
        target = GovernanceOverrideStatus.governance_override_first_approved
        event = "governance_override_first_approved"
    elif record.status == GovernanceOverrideStatus.governance_override_first_approved:
        target = GovernanceOverrideStatus.governance_override_second_approved
        event = "governance_override_second_approved"
    else:
        raise HTTPException(
            status_code=409,
            detail=f"Override in status '{record.status}' cannot be approved.",
        )

    return _transition(
        override_id,
        target,
        f"{_now()} — {event}: approved by {body.approver}",
    )


@router.post("/{override_id}/use", response_model=GovernanceOverrideRecord)
def use_override_for_release(
    override_id: str, body: UseForReleaseRequest
) -> GovernanceOverrideRecord:
    """Mark a fully-approved governance override as used for a release."""
    return _transition(
        override_id,
        GovernanceOverrideStatus.governance_override_used_for_release,
        f"{_now()} — governance_override_used_for_release: release {body.release_tag}",
    )


@router.post("/{override_id}/reject", response_model=GovernanceOverrideRecord)
def reject_override(override_id: str, body: RejectOverrideRequest) -> GovernanceOverrideRecord:
    """Reject a governance override at any non-terminal stage."""
    detail = f" — {body.reason}" if body.reason else ""
    return _transition(
        override_id,
        GovernanceOverrideStatus.governance_override_rejected,
        f"{_now()} — governance_override_rejected: rejected by {body.rejector}{detail}",
    )
