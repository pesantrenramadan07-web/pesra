from datetime import datetime, timezone
from db import db


async def log_audit(user: dict, action: str, module: str, entity_type: str,
                    entity_id: str = None, old_value=None, new_value=None,
                    request=None):
    doc = {
        "user_id": user.get("id") if user else None,
        "user_name": user.get("name") if user else None,
        "action": action,
        "module": module,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "old_value": _sanitize(old_value),
        "new_value": _sanitize(new_value),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_address": request.client.host if request and request.client else None,
        "user_agent": request.headers.get("user-agent") if request else None,
    }
    await db.audit_logs.insert_one(doc)


def _sanitize(value):
    if isinstance(value, dict):
        v = dict(value)
        for k in ["password", "password_hash", "token", "token_hash"]:
            v.pop(k, None)
        return v
    return value
