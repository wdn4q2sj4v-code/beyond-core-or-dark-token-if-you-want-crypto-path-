"""
Release Gate v1
---------------
Consumes a GovernanceVerdict produced by the GovernanceBrain and decides
whether a release is allowed to pass through (OPEN) or is blocked (CLOSED).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from governance_brain import GovernanceBrain, GovernanceVerdict, ReleaseProposal, Verdict


class GateState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class GateDecision:
    gate_state: GateState
    verdict: GovernanceVerdict
    message: str


class ReleaseGate:
    """
    Integration point between GovernanceBrain and the release pipeline.

    Usage::

        gate = ReleaseGate()
        decision = gate.check(proposal)
        if decision.gate_state == GateState.OPEN:
            # proceed with release
    """

    def __init__(self) -> None:
        self._brain = GovernanceBrain()

    def check(self, proposal: ReleaseProposal) -> GateDecision:
        """Run the proposal through the Governance Brain and open/close the gate."""
        verdict = self._brain.evaluate(proposal)

        if verdict.verdict == Verdict.APPROVED:
            state = GateState.OPEN
            message = (
                f"Gate OPEN — '{proposal.title} v{proposal.version}' "
                f"cleared all governance checks. Release may proceed."
            )
        else:
            state = GateState.CLOSED
            message = (
                f"Gate CLOSED — '{proposal.title} v{proposal.version}' "
                f"blocked by Governance Brain. {verdict.reason}"
            )

        return GateDecision(gate_state=state, verdict=verdict, message=message)
