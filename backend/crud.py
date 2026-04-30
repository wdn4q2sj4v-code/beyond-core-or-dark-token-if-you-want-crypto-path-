from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


def create_governance_override_request(
    db: Session, payload: schemas.GovernanceOverrideRequestCreate
) -> models.GovernanceOverrideRequest:
    record = models.GovernanceOverrideRequest(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_governance_override_request(
    db: Session, request_id: int
) -> Optional[models.GovernanceOverrideRequest]:
    return (
        db.query(models.GovernanceOverrideRequest)
        .filter(models.GovernanceOverrideRequest.id == request_id)
        .first()
    )


def list_governance_override_requests(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.GovernanceOverrideRequest]:
    return (
        db.query(models.GovernanceOverrideRequest)
        .order_by(models.GovernanceOverrideRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_governance_override_request(
    db: Session,
    request_id: int,
    payload: schemas.GovernanceOverrideRequestUpdate,
) -> Optional[models.GovernanceOverrideRequest]:
    record = get_governance_override_request(db, request_id)
    if record is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record
