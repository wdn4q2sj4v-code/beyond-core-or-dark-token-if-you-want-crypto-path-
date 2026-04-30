from fastapi import Depends, FastAPI
from pydantic import BaseModel
from typing import List

from governance_brain import GovernanceBrain, ReleaseProposal, REQUIRED_CRITERIA
from release_gate import GateDecision, GateState, ReleaseGate

app = FastAPI(title="BEYOND Core API")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ReleaseProposalRequest(BaseModel):
    title: str
    version: str
    submitted_by: str
    criteria_met: List[str] = []


# ---------------------------------------------------------------------------
# Dependency providers
# ---------------------------------------------------------------------------

def get_governance_brain() -> GovernanceBrain:
    return GovernanceBrain()


def get_release_gate() -> ReleaseGate:
    return ReleaseGate()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_proposal(body: ReleaseProposalRequest) -> ReleaseProposal:
    return ReleaseProposal(
        title=body.title,
        version=body.version,
        submitted_by=body.submitted_by,
        criteria_met=body.criteria_met,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}


@app.get("/governance/criteria")
def list_governance_criteria():
    """Return the full list of required governance criteria for v1."""
    return {"required_criteria": REQUIRED_CRITERIA}


@app.post("/governance/evaluate")
def evaluate_proposal(
    body: ReleaseProposalRequest,
    brain: GovernanceBrain = Depends(get_governance_brain),
):
    """Submit a release proposal to the Governance Brain for evaluation."""
    verdict = brain.evaluate(_to_proposal(body))
    return {
        "proposal_title": verdict.proposal_title,
        "proposal_version": verdict.proposal_version,
        "verdict": verdict.verdict,
        "criteria_passed": verdict.criteria_passed,
        "criteria_failed": verdict.criteria_failed,
        "reason": verdict.reason,
    }


@app.post("/release-gate/check")
def release_gate_check(
    body: ReleaseProposalRequest,
    gate: ReleaseGate = Depends(get_release_gate),
):
    """Run a release proposal through the full Governance Brain → Release Gate pipeline."""
    decision: GateDecision = gate.check(_to_proposal(body))
    return {
        "gate_state": decision.gate_state,
        "message": decision.message,
        "governance_verdict": {
            "verdict": decision.verdict.verdict,
            "criteria_passed": decision.verdict.criteria_passed,
            "criteria_failed": decision.verdict.criteria_failed,
            "reason": decision.verdict.reason,
        },
    }
