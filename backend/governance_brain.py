"""
Governance Brain — proposal/approval state machine.

A Governance Brain instance holds a registry of proposals.  Each proposal
moves through the following states (approved and rejected are both final):

  pending → approved
  pending → rejected

Only approved proposals unlock the Release Gate.

Public API
----------
GovernanceBrain       – in-memory singleton used by the FastAPI app
ProposalIn            – Pydantic model for creating a proposal
ProposalOut           – Pydantic model returned to callers
ProposalStatus        – enum of allowed status values
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProposalIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    release_tag: str = Field(..., min_length=1, max_length=100,
                             description="Release identifier this proposal gates.")


class ProposalOut(BaseModel):
    id: str
    title: str
    description: str
    release_tag: str
    status: ProposalStatus
    created_at: datetime
    resolved_at: Optional[datetime]


class GovernanceBrain:
    """In-memory governance store.  Swap for a DB-backed version in production."""

    def __init__(self) -> None:
        self._proposals: Dict[str, ProposalOut] = {}

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list_proposals(self) -> List[ProposalOut]:
        return list(self._proposals.values())

    def get_proposal(self, proposal_id: str) -> Optional[ProposalOut]:
        return self._proposals.get(proposal_id)

    def is_release_approved(self, release_tag: str) -> bool:
        """Return True only when at least one approved proposal exists for the tag."""
        return any(
            p.status == ProposalStatus.APPROVED and p.release_tag == release_tag
            for p in self._proposals.values()
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def submit_proposal(self, data: ProposalIn) -> ProposalOut:
        proposal = ProposalOut(
            id=str(uuid.uuid4()),
            title=data.title,
            description=data.description,
            release_tag=data.release_tag,
            status=ProposalStatus.PENDING,
            created_at=datetime.now(tz=timezone.utc),
            resolved_at=None,
        )
        self._proposals[proposal.id] = proposal
        return proposal

    def _resolve(self, proposal_id: str, new_status: ProposalStatus) -> Optional[ProposalOut]:
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return None
        if proposal.status != ProposalStatus.PENDING:
            raise ValueError(
                f"Proposal '{proposal_id}' is already resolved "
                f"(status={proposal.status.value})."
            )
        updated = proposal.model_copy(update={
            "status": new_status,
            "resolved_at": datetime.now(tz=timezone.utc),
        })
        self._proposals[proposal_id] = updated
        return updated

    def approve_proposal(self, proposal_id: str) -> Optional[ProposalOut]:
        return self._resolve(proposal_id, ProposalStatus.APPROVED)

    def reject_proposal(self, proposal_id: str) -> Optional[ProposalOut]:
        return self._resolve(proposal_id, ProposalStatus.REJECTED)
