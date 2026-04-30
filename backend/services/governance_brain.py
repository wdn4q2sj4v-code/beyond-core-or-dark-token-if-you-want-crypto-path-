"""Governance Brain service.

The Governance Brain evaluates whether a release may proceed.  If a policy
rule is violated the service returns a structured decision explaining why the
release is blocked.  The actual policy logic is intentionally pluggable via
``policy_rules`` so that it can be extended without changing the calling code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class GovernanceDecision:
    """Outcome of a Governance Brain evaluation.

    Attributes:
        blocked: ``True`` when the release must not proceed.
        reason: Human-readable explanation of the decision.
        policy: Name of the policy rule that was triggered (empty string when
            not blocked).
        details: Arbitrary extra data a policy rule may attach to the decision.
    """

    blocked: bool
    reason: str = ""
    policy: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for JSON responses."""
        return {
            "blocked": self.blocked,
            "reason": self.reason,
            "policy": self.policy,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Built-in policy rules
# ---------------------------------------------------------------------------

PolicyRule = Callable[[dict[str, Any]], GovernanceDecision | None]
"""A callable that inspects a release payload and returns a
:class:`GovernanceDecision` if the rule triggers, or ``None`` to pass."""


def _require_reviewer(payload: dict[str, Any]) -> GovernanceDecision | None:
    """Block releases that have no assigned reviewer."""
    if not payload.get("reviewer_id"):
        return GovernanceDecision(
            blocked=True,
            reason="A reviewer must be assigned before a release can be published.",
            policy="require_reviewer",
        )
    return None


def _require_approval(payload: dict[str, Any]) -> GovernanceDecision | None:
    """Block releases whose approval status is not 'approved'."""
    status = payload.get("approval_status", "")
    if status != "approved":
        return GovernanceDecision(
            blocked=True,
            reason=f"Release approval status is '{status}'; must be 'approved'.",
            policy="require_approval",
            details={"approval_status": status},
        )
    return None


DEFAULT_POLICY_RULES: list[PolicyRule] = [
    _require_reviewer,
    _require_approval,
]


# ---------------------------------------------------------------------------
# GovernanceBrain
# ---------------------------------------------------------------------------


class GovernanceBrain:
    """Evaluates release payloads against a configurable set of policy rules.

    Args:
        policy_rules: Ordered list of callables to run against the payload.
            Evaluation stops at the first rule that returns a blocked decision.
            If omitted, :data:`DEFAULT_POLICY_RULES` are used.

    Example::

        brain = GovernanceBrain()
        decision = brain.evaluate({"reviewer_id": 42, "approval_status": "approved"})
        assert not decision.blocked
    """

    def __init__(
        self,
        policy_rules: list[PolicyRule] | None = None,
    ) -> None:
        self._rules = policy_rules if policy_rules is not None else DEFAULT_POLICY_RULES

    def evaluate(self, payload: dict[str, Any]) -> GovernanceDecision:
        """Run all policy rules against *payload*.

        Returns the first blocking decision found, or an unblocked decision
        when all rules pass.

        Args:
            payload: Arbitrary dict describing the release to be evaluated.

        Returns:
            A :class:`GovernanceDecision` instance.
        """
        for rule in self._rules:
            decision = rule(payload)
            if decision is not None and decision.blocked:
                return decision
        return GovernanceDecision(blocked=False)
