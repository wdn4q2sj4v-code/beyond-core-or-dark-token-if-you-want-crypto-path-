"""
Governance Brain — release-gate evaluation engine for BEYOND.

The ``GovernanceBrain`` analyses a ``NotificationRuleApprovalRequest`` and
produces a structured decision: ``"approved"`` or ``"rejected"``.  It assigns a
*governance score* between 0.0 and 1.0, collects named *signals* that
contributed to the score and records the *reasons* behind the final decision.

Scores are computed from a configurable set of signal evaluators.  Each signal
contributes a weighted partial score.  If the aggregate score meets or exceeds
``APPROVAL_THRESHOLD`` the decision is ``"approved"``; otherwise it is
``"rejected"``.

Signals evaluated
-----------------
- **rule_name_provided** – the request has a non-empty ``rule_name``.
- **description_provided** – the request supplies an explanatory ``description``.
- **has_requester** – the request is associated with a known user.
- **status_pending** – the request is still in ``pending`` status (not already
  decided).
- **requester_role_member** – the requester holds at least the ``member`` role,
  which verifies that the user is a recognised participant.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from models import NotificationRuleApprovalRequest

logger = logging.getLogger(__name__)

APPROVAL_THRESHOLD = 0.6

_SIGNAL_WEIGHTS: dict[str, float] = {
    "rule_name_provided": 0.25,
    "description_provided": 0.20,
    "has_requester": 0.25,
    "status_pending": 0.15,
    "requester_role_member": 0.15,
}


def _is_nonempty_string(value: object) -> bool:
    """Return ``True`` when *value* is a non-empty string after stripping whitespace."""
    return isinstance(value, str) and bool(value.strip())


@dataclass
class GovernanceBrain:
    """Encapsulates the result of a release-gate governance evaluation.

    Attributes:
        decision: ``"approved"`` if the request meets the governance threshold,
            ``"rejected"`` otherwise.
        governance_score: Aggregate weighted score in the range ``[0.0, 1.0]``.
        signals: Mapping of signal name to boolean value captured during
            evaluation.
        reasons: Human-readable explanations for the final decision.
        signals_json: ``signals`` serialised as a JSON string (suitable for
            storage in the ``AuditLog.after`` snapshot).
        reasons_json: ``reasons`` serialised as a JSON string.
    """

    decision: str = "rejected"
    governance_score: float = 0.0
    signals: dict[str, bool] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    @property
    def signals_json(self) -> str:
        return json.dumps(self.signals)

    @property
    def reasons_json(self) -> str:
        return json.dumps(self.reasons)

    @classmethod
    def evaluate(
        cls,
        db: Session,
        approval_request: NotificationRuleApprovalRequest,
    ) -> "GovernanceBrain":
        """Evaluate release eligibility for *approval_request*.

        Args:
            db: Active SQLAlchemy session (reserved for future signal lookups).
            approval_request: The notification rule approval request to evaluate.

        Returns:
            A fully populated ``GovernanceBrain`` instance.
        """
        brain = cls()

        # --- signal evaluation ------------------------------------------------
        brain.signals["rule_name_provided"] = _is_nonempty_string(approval_request.rule_name)
        brain.signals["description_provided"] = _is_nonempty_string(approval_request.description)
        brain.signals["has_requester"] = approval_request.requester_id is not None
        brain.signals["status_pending"] = approval_request.status == "pending"
        brain.signals["requester_role_member"] = (
            approval_request.requester is not None
            and approval_request.requester.role in {"member", "admin", "governance"}
        )

        # --- aggregate score --------------------------------------------------
        brain.governance_score = round(
            sum(
                _SIGNAL_WEIGHTS[name] * (1.0 if passed else 0.0)
                for name, passed in brain.signals.items()
            ),
            4,
        )

        # --- decision ---------------------------------------------------------
        if brain.governance_score >= APPROVAL_THRESHOLD:
            brain.decision = "approved"
            brain.reasons.append(
                f"Governance score {brain.governance_score} meets the approval"
                f" threshold of {APPROVAL_THRESHOLD}."
            )
        else:
            brain.decision = "rejected"
            brain.reasons.append(
                f"Governance score {brain.governance_score} is below the approval"
                f" threshold of {APPROVAL_THRESHOLD}."
            )

        failing = [name for name, passed in brain.signals.items() if not passed]
        if failing:
            brain.reasons.append(
                "The following signals were not satisfied: " + ", ".join(failing) + "."
            )

        logger.info(
            "GovernanceBrain evaluation complete: decision=%s score=%s",
            brain.decision,
            brain.governance_score,
        )
        return brain
