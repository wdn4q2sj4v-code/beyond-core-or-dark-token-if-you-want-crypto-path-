from datetime import datetime, timezone
from models import GovernanceOverrideRequest, OverrideStatus


def approve_governance_override(db, *, override_id: int, user_id: int):
    row = db.query(GovernanceOverrideRequest).filter(
        GovernanceOverrideRequest.id == override_id
    ).first()

    if not row:
        raise ValueError("Override request not found.")

    if row.status != OverrideStatus.pending:
        raise ValueError("Only pending override requests can be approved.")

    if row.created_by_user_id == user_id:
        raise ValueError("Creator cannot approve their own override.")

    if row.first_approved_by_user_id == user_id:
        raise ValueError("Same user cannot approve twice.")

    now = datetime.now(timezone.utc)

    if row.first_approved_by_user_id is None:
        row.first_approved_by_user_id = user_id
        row.first_approved_at = now

    else:
        row.second_approved_by_user_id = user_id
        row.second_approved_at = now
        row.status = OverrideStatus.approved

    db.commit()
    db.refresh(row)
    return row
