"""
Governance Brain v1
-------------------
Evaluates a release proposal against the BEYOND governance ruleset and
returns a structured verdict that the Release Gate consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


# ---------------------------------------------------------------------------
# Required governance criteria that every release MUST satisfy (v1 ruleset)
# ---------------------------------------------------------------------------
REQUIRED_CRITERIA: List[str] = [
    "verified_care",
    "stewardship_review",
    "peace_simulation_pass",
    "essential_value_confirmed",
    "guardian_earth_approval",
]


class Verdict(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ReleaseProposal:
    title: str
    version: str
    submitted_by: str
    criteria_met: List[str] = field(default_factory=list)


@dataclass
class GovernanceVerdict:
    proposal_title: str
    proposal_version: str
    verdict: Verdict
    criteria_passed: List[str]
    criteria_failed: List[str]
    reason: str


class GovernanceBrain:
    """
    Evaluates a ReleaseProposal against the required governance criteria and
    produces a GovernanceVerdict.
    """

    def evaluate(self, proposal: ReleaseProposal) -> GovernanceVerdict:
        criteria_passed = [c for c in REQUIRED_CRITERIA if c in proposal.criteria_met]
        criteria_failed = [c for c in REQUIRED_CRITERIA if c not in proposal.criteria_met]

        if criteria_failed:
            verdict = Verdict.REJECTED
            reason = (
                f"Release '{proposal.title} v{proposal.version}' failed governance. "
                f"Missing criteria: {', '.join(criteria_failed)}."
            )
        else:
            verdict = Verdict.APPROVED
            reason = (
                f"Release '{proposal.title} v{proposal.version}' passed all governance criteria."
            )

        return GovernanceVerdict(
            proposal_title=proposal.title,
            proposal_version=proposal.version,
            verdict=verdict,
            criteria_passed=criteria_passed,
            criteria_failed=criteria_failed,
            reason=reason,
        )
