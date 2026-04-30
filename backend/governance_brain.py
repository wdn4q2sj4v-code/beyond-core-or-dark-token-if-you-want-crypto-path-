"""Governance Brain – the central decision engine.

Consumes the output of policy-gate evaluation and produces a GovernanceDecision.
"""
from __future__ import annotations

from typing import List

from models import ApprovalRequest, Decision, GovernanceDecision
from policy_gates import evaluate_all_gates


def run_governance_brain(req: ApprovalRequest) -> GovernanceDecision:
    """Evaluate all policy gates and decide ALLOWED or BLOCKED.

    Rules:
    * If *any* gate returns violations → BLOCKED with full reason list.
    * If all gates pass → ALLOWED.
    """
    violations: List[str] = evaluate_all_gates(req)

    if violations:
        return GovernanceDecision(
            request_id=req.request_id,
            decision=Decision.BLOCKED,
            reasons=violations,
        )

    return GovernanceDecision(
        request_id=req.request_id,
        decision=Decision.ALLOWED,
        reasons=["All policy gates passed. Request is approved for release."],
    )
