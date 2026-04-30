from fastapi import APIRouter

from backend.database import approve_governance_override
from backend.models import GovernanceOverrideApproveRequest, GovernanceOverrideResponse

router = APIRouter()


@router.post(
    "/admin/governance-overrides/{override_id}/approve",
    response_model=GovernanceOverrideResponse,
)
def approve_override(
    override_id: str, body: GovernanceOverrideApproveRequest
) -> GovernanceOverrideResponse:
    row = approve_governance_override(
        override_id=override_id,
        approved_by=body.approved_by,
        notes=body.notes,
    )
    return GovernanceOverrideResponse.model_validate(row)
