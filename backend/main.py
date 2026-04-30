from fastapi import FastAPI, HTTPException

from governance_brain import GovernanceBrain, ProposalIn, ProposalOut
from release_gate import ReleaseGate, GateStatus

app = FastAPI(title="BEYOND Core", version="1.0.0")

# Shared singletons wired together (Governance Brain → Release Gate)
_brain = GovernanceBrain()
_gate = ReleaseGate(_brain)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


# ---------------------------------------------------------------------------
# Governance Brain endpoints
# ---------------------------------------------------------------------------

@app.post("/governance/proposals", response_model=ProposalOut, status_code=201,
          tags=["Governance"])
def submit_proposal(data: ProposalIn):
    """Submit a new governance proposal for a release tag."""
    return _brain.submit_proposal(data)


@app.get("/governance/proposals", response_model=list[ProposalOut], tags=["Governance"])
def list_proposals():
    """List all governance proposals."""
    return _brain.list_proposals()


@app.get("/governance/proposals/{proposal_id}", response_model=ProposalOut,
         tags=["Governance"])
def get_proposal(proposal_id: str):
    """Get a single governance proposal by ID."""
    proposal = _brain.get_proposal(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return proposal


@app.post("/governance/proposals/{proposal_id}/approve", response_model=ProposalOut,
          tags=["Governance"])
def approve_proposal(proposal_id: str):
    """Approve a governance proposal, unlocking its release tag."""
    try:
        result = _brain.approve_proposal(proposal_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return result


@app.post("/governance/proposals/{proposal_id}/reject", response_model=ProposalOut,
          tags=["Governance"])
def reject_proposal(proposal_id: str):
    """Reject a governance proposal."""
    try:
        result = _brain.reject_proposal(proposal_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return result


# ---------------------------------------------------------------------------
# Release Gate endpoints
# ---------------------------------------------------------------------------

@app.get("/release-gate/{release_tag}", response_model=GateStatus, tags=["Release Gate"])
def check_release_gate(release_tag: str):
    """
    Query the Release Gate for a given release tag.

    Returns ``open: true`` only when the Governance Brain has at least one
    approved proposal for that tag.
    """
    return _gate.check_gate(release_tag)
