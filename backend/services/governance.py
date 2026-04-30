from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import GovernanceOverride


def approve_governance_override(
    db: Session, override_id: int, approved_by: str
) -> GovernanceOverride:
    """Approve a pending governance override.

    Raises 404 if the override does not exist and 409 if it has already
    been approved or rejected.
    """
    override: GovernanceOverride | None = (
        db.query(GovernanceOverride).filter(GovernanceOverride.id == override_id).first()
    )

    if override is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Governance override {override_id} not found.",
        )

    if override.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Governance override {override_id} cannot be approved "
                f"because its current status is '{override.status}'."
            ),
        )

    override.status = "approved"
    override.approved_at = datetime.now(timezone.utc)
    override.approved_by = approved_by
    db.commit()
    db.refresh(override)
    return override
