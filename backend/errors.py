"""Custom exceptions and FastAPI exception handlers for the BEYOND backend."""

from fastapi import Request
from fastapi.responses import JSONResponse


class GovernanceBrainBlockError(Exception):
    """Raised when the Governance Brain blocks a release.

    Attributes:
        request_id: Identifier of the release item that was blocked.
        governance_decision: Structured decision payload returned by the
            Governance Brain (e.g. reason, policy, reviewer notes).
    """

    def __init__(self, request_id: str, governance_decision: dict) -> None:
        self.request_id = request_id
        self.governance_decision = governance_decision
        super().__init__("Release blocked by Governance Brain.")


async def governance_brain_block_handler(
    request: Request, exc: GovernanceBrainBlockError
) -> JSONResponse:
    """Return a 422 response whose ``detail`` matches the shape the frontend expects.

    The frontend checks::

        if (err.detail?.message === "Release blocked by Governance Brain.") {
            setGateView({
                requestId: item.id,
                result: err.detail.governance_decision,
                type: "governance_brain_block",
            });
        }

    So the response body must be::

        {
            "detail": {
                "message": "Release blocked by Governance Brain.",
                "governance_decision": { ... }
            }
        }
    """
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "message": "Release blocked by Governance Brain.",
                "governance_decision": exc.governance_decision,
            }
        },
    )
