"""
Release Gate — controls whether a release is permitted to proceed.

The gate queries the Governance Brain: a release_tag is allowed through
only when at least one governance proposal for that tag has been approved.

Public API
----------
ReleaseGate   – thin facade over GovernanceBrain
GateStatus    – Pydantic model returned to callers
"""

from __future__ import annotations

from pydantic import BaseModel

from governance_brain import GovernanceBrain


class GateStatus(BaseModel):
    release_tag: str
    open: bool
    reason: str


class ReleaseGate:
    """Wraps a GovernanceBrain and exposes a single check_gate method."""

    def __init__(self, brain: GovernanceBrain) -> None:
        self._brain = brain

    def check_gate(self, release_tag: str) -> GateStatus:
        approved = self._brain.is_release_approved(release_tag)
        if approved:
            return GateStatus(
                release_tag=release_tag,
                open=True,
                reason="Governance proposal approved — release is permitted.",
            )
        return GateStatus(
            release_tag=release_tag,
            open=False,
            reason="No approved governance proposal found — release is blocked.",
        )
