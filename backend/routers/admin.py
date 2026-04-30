from fastapi import APIRouter

from crud import create_governance_override_request
from models import GovernanceOverrideCreate, GovernanceOverrideRow

router = APIRouter()


@router.post("/admin/governance-overrides", response_model=GovernanceOverrideRow, status_code=201)
def create_override(payload: GovernanceOverrideCreate) -> GovernanceOverrideRow:
    row = create_governance_override_request(payload)
    return row
