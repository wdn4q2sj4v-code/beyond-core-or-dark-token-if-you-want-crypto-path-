"""Release endpoints.

POST /releases/{item_id}/publish
    Attempt to publish a release item.  The request body is passed through
    the :class:`~services.governance_brain.GovernanceBrain`; if any policy
    rule blocks the release a :class:`~errors.GovernanceBrainBlockError` is
    raised so that the registered exception handler can return the structured
    error response that the frontend expects.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any

from errors import GovernanceBrainBlockError
from services.governance_brain import GovernanceBrain

router = APIRouter(prefix="/releases", tags=["releases"])

_governance_brain = GovernanceBrain()


class PublishRequest(BaseModel):
    """Payload for a publish attempt."""

    reviewer_id: int | None = None
    approval_status: str = "pending"
    metadata: dict[str, Any] = Field(default_factory=dict)


class PublishResponse(BaseModel):
    """Returned when a release is successfully published."""

    item_id: str
    status: str = "published"


@router.post("/{item_id}/publish", response_model=PublishResponse)
def publish_release(item_id: str, body: PublishRequest) -> PublishResponse:
    """Attempt to publish the release identified by *item_id*.

    The full request body is evaluated by the Governance Brain.  If a policy
    rule is triggered, a ``422`` response is returned with the shape::

        {
            "detail": {
                "message": "Release blocked by Governance Brain.",
                "governance_decision": { ... }
            }
        }

    This matches the error-handling code in the frontend::

        if (err.detail?.message === "Release blocked by Governance Brain.") {
            setGateView({
                requestId: item.id,
                result: err.detail.governance_decision,
                type: "governance_brain_block",
            });
        }

    Args:
        item_id: Identifier of the release item to publish.
        body: Release metadata used by governance policy rules.

    Returns:
        :class:`PublishResponse` on success.

    Raises:
        :class:`~errors.GovernanceBrainBlockError`: When governance blocks the release.
    """
    payload = {
        "item_id": item_id,
        "reviewer_id": body.reviewer_id,
        "approval_status": body.approval_status,
        **body.metadata,
    }

    decision = _governance_brain.evaluate(payload)

    if decision.blocked:
        raise GovernanceBrainBlockError(
            request_id=item_id,
            governance_decision=decision.to_dict(),
        )

    return PublishResponse(item_id=item_id)
