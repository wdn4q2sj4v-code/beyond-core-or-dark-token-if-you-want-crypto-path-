from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/governance-override-requests",
    tags=["governance-override-requests"],
)


@router.post(
    "/",
    response_model=schemas.GovernanceOverrideRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    payload: schemas.GovernanceOverrideRequestCreate,
    db: Session = Depends(get_db),
):
    return crud.create_governance_override_request(db, payload)


@router.get("/", response_model=List[schemas.GovernanceOverrideRequestRead])
def list_requests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_governance_override_requests(db, skip=skip, limit=limit)


@router.get("/{request_id}", response_model=schemas.GovernanceOverrideRequestRead)
def get_request(request_id: int, db: Session = Depends(get_db)):
    record = crud.get_governance_override_request(db, request_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Governance override request not found",
        )
    return record


@router.patch("/{request_id}", response_model=schemas.GovernanceOverrideRequestRead)
def update_request(
    request_id: int,
    payload: schemas.GovernanceOverrideRequestUpdate,
    db: Session = Depends(get_db),
):
    record = crud.update_governance_override_request(db, request_id, payload)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Governance override request not found",
        )
    return record
