from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import GovernanceOverrideApproveRequest, GovernanceOverrideResponse
from ..services.governance import approve_governance_override

router = APIRouter(tags=["admin"])


@router.post(
    "/admin/governance-overrides/{override_id}/approve",
    response_model=GovernanceOverrideResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a governance override",
)
def approve_override(
    override_id: int,
    body: GovernanceOverrideApproveRequest,
    db: Session = Depends(get_db),
) -> GovernanceOverrideResponse:
    """Approve a pending governance override by its ID.

    Returns the updated override record.
    Responds with **404** if the override is not found, or **409** if it is
    already approved or rejected.
    """
    approved_override = approve_governance_override(db=db, override_id=override_id, approved_by=body.approved_by)
    return GovernanceOverrideResponse.model_validate(approved_override)
