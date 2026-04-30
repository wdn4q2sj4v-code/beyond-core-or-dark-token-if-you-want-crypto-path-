from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException

# In-memory store for governance overrides
_overrides: dict[str, dict] = {
    "override-1": {
        "id": "override-1",
        "status": "pending",
        "approved_by": None,
        "notes": None,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "approved_at": None,
    },
}


def approve_governance_override(
    override_id: str, approved_by: str, notes: Optional[str]
) -> dict:
    override = _overrides.get(override_id)
    if override is None:
        raise HTTPException(status_code=404, detail="Governance override not found")
    if override["status"] == "approved":
        raise HTTPException(
            status_code=409, detail="Governance override is already approved"
        )
    override["status"] = "approved"
    override["approved_by"] = approved_by
    override["notes"] = notes
    override["approved_at"] = datetime.now(tz=timezone.utc)
    return override
