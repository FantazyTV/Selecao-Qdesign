from datetime import datetime, timezone


def audit_entry(action: str, details: dict) -> dict:
    return {
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
