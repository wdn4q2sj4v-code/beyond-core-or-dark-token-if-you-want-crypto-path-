from sqlalchemy.orm import Session

from models import GovernanceOverrideRequest


def find_valid_dual_override(db: Session, *, approval_request_id: int):
    """Return the most recent fully dual-approved governance override for the
    given approval request, or ``None`` if no such record exists.

    A *valid dual override* requires:
    - ``status == "approved"``
    - both ``first_approved_by_user_id`` and ``second_approved_by_user_id``
      are non-NULL (i.e. two distinct approvers have signed off).
    """
    return (
        db.query(GovernanceOverrideRequest)
        .filter(GovernanceOverrideRequest.approval_request_id == approval_request_id)
        .filter(GovernanceOverrideRequest.status == "approved")
        .filter(GovernanceOverrideRequest.first_approved_by_user_id.isnot(None))
        .filter(GovernanceOverrideRequest.second_approved_by_user_id.isnot(None))
        .order_by(GovernanceOverrideRequest.created_at.desc())
        .first()
    )
