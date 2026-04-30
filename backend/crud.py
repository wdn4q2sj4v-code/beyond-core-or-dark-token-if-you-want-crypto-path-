from sqlalchemy.orm import Session

from models import GovernanceOverrideRequest


def create_governance_override_request(
    db: Session,
    *,
    approval_request_id: int,
    governance_brain_decision_id: int,
    reason: str,
    user_id: int,
) -> GovernanceOverrideRequest:
    if not reason.strip():
        raise ValueError("Override reason is required.")

    row = GovernanceOverrideRequest(
        approval_request_id=approval_request_id,
        governance_brain_decision_id=governance_brain_decision_id,
        reason=reason.strip(),
        created_by_user_id=user_id,
        status="pending",
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row
