"""Policy gates evaluated before the Governance Brain makes its final decision.

Each gate is a callable that accepts an ApprovalRequest and returns a list of
violation strings.  An empty list means the gate passed.
"""
from __future__ import annotations

from typing import Callable, List

from models import ApprovalRequest

# ---------------------------------------------------------------------------
# Individual policy gates
# ---------------------------------------------------------------------------

BANNED_ACTIONS: set[str] = {"nuke", "purge_all", "mass_delete"}


def gate_banned_actions(req: ApprovalRequest) -> List[str]:
    """Block explicitly banned action keywords."""
    if req.action.lower() in BANNED_ACTIONS:
        return [f"Action '{req.action}' is on the banned-actions list."]
    return []


def gate_requester_identity(req: ApprovalRequest) -> List[str]:
    """Require a non-empty, non-anonymous requester identity."""
    if not req.requester or req.requester.strip().lower() in ("", "anonymous", "unknown"):
        return ["Requester identity must be verified (no anonymous requests)."]
    return []


def gate_payload_size(req: ApprovalRequest) -> List[str]:
    """Reject payloads that are unreasonably large (> 50 keys)."""
    if len(req.payload) > 50:
        return [f"Payload exceeds maximum allowed size (got {len(req.payload)} keys, max 50)."]
    return []


def gate_sensitive_keywords(req: ApprovalRequest) -> List[str]:
    """Flag actions containing sensitive keywords that need extra scrutiny."""
    sensitive = {"delete", "drop", "truncate", "override", "escalate"}
    hits = [kw for kw in sensitive if kw in req.action.lower()]
    if hits:
        return [f"Action contains sensitive keyword(s): {', '.join(hits)}."]
    return []


# ---------------------------------------------------------------------------
# Registry – add new gates here
# ---------------------------------------------------------------------------

POLICY_GATES: List[Callable[[ApprovalRequest], List[str]]] = [
    gate_banned_actions,
    gate_requester_identity,
    gate_payload_size,
    gate_sensitive_keywords,
]


def evaluate_all_gates(req: ApprovalRequest) -> List[str]:
    """Run every registered gate and collect all violations."""
    violations: List[str] = []
    for gate in POLICY_GATES:
        violations.extend(gate(req))
    return violations
