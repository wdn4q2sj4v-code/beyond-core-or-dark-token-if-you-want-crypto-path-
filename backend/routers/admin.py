from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth import require_admin
from database import get_db
from models import GovernanceOverrideRequest, OverrideStatus

router = APIRouter(prefix="/admin", tags=["admin"])

_MAX_PAGE_SIZE = 100
_DEFAULT_PAGE_SIZE = 20


@router.get("/governance-overrides")
def list_overrides(
    # --- pagination ---
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=_MAX_PAGE_SIZE, description="Maximum records to return")
    ] = _DEFAULT_PAGE_SIZE,
    # --- filters ---
    status: Annotated[
        OverrideStatus | None, Query(description="Filter by override status")
    ] = None,
    created_after: Annotated[
        datetime | None, Query(description="Return only records created after this UTC timestamp")
    ] = None,
    created_before: Annotated[
        datetime | None, Query(description="Return only records created before this UTC timestamp")
    ] = None,
    requester_id: Annotated[
        str | None, Query(description="Filter by requester identifier")
    ] = None,
    # --- auth + db ---
    current_admin: Annotated[dict, Depends(require_admin)] = None,
    db: Session = Depends(get_db),
):
    query = db.query(GovernanceOverrideRequest)

    if status is not None:
        query = query.filter(GovernanceOverrideRequest.status == status)
    if created_after is not None:
        query = query.filter(GovernanceOverrideRequest.created_at >= created_after)
    if created_before is not None:
        query = query.filter(GovernanceOverrideRequest.created_at <= created_before)
    if requester_id is not None:
        query = query.filter(GovernanceOverrideRequest.requester_id == requester_id)

    total = query.count()
    items = (
        query.order_by(GovernanceOverrideRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": items,
    }
