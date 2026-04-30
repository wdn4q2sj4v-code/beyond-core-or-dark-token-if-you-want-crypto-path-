"""
GovernanceBrain — evaluates the release eligibility of a notification rule
approval request and produces a structured governance decision.

The brain inspects the request's metadata and derives a composite
``governance_score`` (0.0–1.0) from a set of weighted signals.  Requests
scoring above 0.75 are automatically approved; those below 0.4 are rejected;
everything else is routed for human review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from models import NotificationRuleApprovalRequest


_APPROVE_THRESHOLD = 0.75
_REJECT_THRESHOLD = 0.40

_STATUS_WEIGHTS: Dict[str, float] = {
    "approved": 1.0,
    "pending": 0.5,
    "rejected": 0.0,
}


@dataclass
class GovernanceBrain:
    """Evaluates release eligibility for a ``NotificationRuleApprovalRequest``.

    Attributes:
        decision: One of ``"approved"``, ``"rejected"``, or ``"pending_review"``.
        governance_score: Composite score in the range ``[0.0, 1.0]``.
        signals_json: Dict of named signals and their individual scores.
        reasons_json: Human-readable list explaining the decision.
    """

    decision: str = field(init=False, default="pending_review")
    governance_score: float = field(init=False, default=0.0)
    signals_json: Dict[str, Any] = field(init=False, default_factory=dict)
    reasons_json: List[str] = field(init=False, default_factory=list)

    def evaluate(self, request: NotificationRuleApprovalRequest) -> "GovernanceBrain":
        """Run the governance evaluation against *request* and populate all fields.

        Args:
            request: The approval request to evaluate.

        Returns:
            *self* — allows chaining: ``brain.evaluate(request)``.
        """
        signals: Dict[str, float] = {}
        reasons: List[str] = []

        # Signal 1: current approval status
        status_score = _STATUS_WEIGHTS.get(request.status, 0.5)
        signals["approval_status"] = status_score
        reasons.append(
            f"Approval status '{request.status}' contributes score {status_score:.2f}"
        )

        # Signal 2: rule name completeness (non-empty, reasonably long)
        rule_name = (request.rule_name or "").strip()
        name_score = min(len(rule_name) / 20.0, 1.0) if rule_name else 0.0
        signals["rule_name_completeness"] = name_score
        reasons.append(
            f"Rule name length {len(rule_name)} chars gives completeness score {name_score:.2f}"
        )

        # Signal 3: description provided
        desc = (request.description or "").strip()
        description_score = 1.0 if desc else 0.0
        signals["description_present"] = description_score
        if desc:
            reasons.append("Description is present, boosting confidence")
        else:
            reasons.append("No description provided; confidence reduced")

        # Signal 4: requester identity populated
        requester = (request.requested_by or "").strip()
        requester_score = 1.0 if requester else 0.0
        signals["requester_identity"] = requester_score
        if requester:
            reasons.append(f"Requester identity '{requester}' is populated")
        else:
            reasons.append("Requester identity is missing; confidence reduced")

        # Weighted composite score
        weights = {
            "approval_status": 0.50,
            "rule_name_completeness": 0.20,
            "description_present": 0.15,
            "requester_identity": 0.15,
        }
        composite = sum(signals[k] * weights[k] for k in weights)

        self.signals_json = {k: round(v, 4) for k, v in signals.items()}
        self.governance_score = round(composite, 4)
        self.reasons_json = reasons

        if composite >= _APPROVE_THRESHOLD:
            self.decision = "approved"
            reasons.append(
                f"Composite score {composite:.4f} ≥ {_APPROVE_THRESHOLD} → approved"
            )
        elif composite < _REJECT_THRESHOLD:
            self.decision = "rejected"
            reasons.append(
                f"Composite score {composite:.4f} < {_REJECT_THRESHOLD} → rejected"
            )
        else:
            self.decision = "pending_review"
            reasons.append(
                f"Composite score {composite:.4f} in review range"
                f" [{_REJECT_THRESHOLD}, {_APPROVE_THRESHOLD}) → pending_review"
            )

        return self
