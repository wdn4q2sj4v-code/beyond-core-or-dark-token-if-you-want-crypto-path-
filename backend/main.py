from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException

import audit
from governance_brain import run_governance_brain
from models import (
    ApprovalRequest,
    AuditEntry,
    Decision,
    GovernanceDecision,
    OverrideRequest,
)

app = FastAPI(title="BEYOND Governance API")

# ---------------------------------------------------------------------------
# In-memory store of decisions keyed by request_id (replaces a real DB)
# ---------------------------------------------------------------------------
_decisions: dict[str, GovernanceDecision] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def read_root() -> dict:
    return {"message": "BEYOND is alive"}


@app.post("/approve", response_model=GovernanceDecision, summary="Submit an approval request")
def approve(req: ApprovalRequest) -> GovernanceDecision:
    """Evaluate policy gates → run Governance Brain → release or block.

    * **ALLOWED** – all gates passed; the request is cleared for release.
    * **BLOCKED** – one or more gates failed; response includes blocking reasons.
    """
    audit.record(
        event="REQUEST_RECEIVED",
        request_id=req.request_id,
        actor=req.requester,
        detail=f"Action: {req.action}",
    )

    decision = run_governance_brain(req)
    _decisions[req.request_id] = decision

    audit.record(
        event=f"DECISION_{decision.decision.value}",
        request_id=req.request_id,
        actor="governance_brain",
        detail="; ".join(decision.reasons),
    )

    return decision


@app.post(
    "/override",
    response_model=GovernanceDecision,
    summary="Superadmin override for a blocked request",
)
def override(req: OverrideRequest) -> GovernanceDecision:
    """Allow a superadmin to override a BLOCKED decision.

    Raises **404** if the request_id was never seen.
    Raises **400** if the decision is not currently BLOCKED.
    """
    decision = _decisions.get(req.request_id)
    if decision is None:
        raise HTTPException(status_code=404, detail=f"No decision found for request_id '{req.request_id}'.")

    if decision.decision != Decision.BLOCKED:
        raise HTTPException(
            status_code=400,
            detail=f"Request '{req.request_id}' is not blocked (current status: {decision.decision.value}).",
        )

    overridden = GovernanceDecision(
        request_id=req.request_id,
        decision=Decision.OVERRIDDEN,
        reasons=[
            f"Superadmin override by '{req.superadmin}'.",
            f"Justification: {req.justification}",
        ],
    )
    _decisions[req.request_id] = overridden

    audit.record(
        event="SUPERADMIN_OVERRIDE",
        request_id=req.request_id,
        actor=req.superadmin,
        detail=req.justification,
    )

    return overridden


@app.get("/audit", response_model=List[AuditEntry], summary="Retrieve the full audit log")
def get_audit_log() -> List[AuditEntry]:
    """Return every audited event in chronological order."""
    return audit.get_all()

