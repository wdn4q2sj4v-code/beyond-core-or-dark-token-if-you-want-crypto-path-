import threading
from datetime import datetime, timezone
from typing import List

from models import GovernanceOverrideCreate, GovernanceOverrideRow

_overrides_store: List[GovernanceOverrideRow] = []
_next_id: int = 1
_lock = threading.Lock()


def create_governance_override_request(
    payload: GovernanceOverrideCreate,
) -> GovernanceOverrideRow:
    global _next_id
    with _lock:
        row = GovernanceOverrideRow(
            id=_next_id,
            target_policy=payload.target_policy,
            override_value=payload.override_value,
            reason=payload.reason,
            requested_by=payload.requested_by,
            created_at=datetime.now(tz=timezone.utc),
            status="pending",
        )
        _overrides_store.append(row)
        _next_id += 1
    return row
