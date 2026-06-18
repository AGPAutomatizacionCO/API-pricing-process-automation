import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BACKEND_DIR / "logs"

CATEGORY_FILES = {
    "audit": "audit.jsonl",
    "auth": "auth.jsonl",
    "access_denied": "access_denied.jsonl",
    "errors": "errors.jsonl",
}


def ensure_log_files() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    for filename in CATEGORY_FILES.values():
        file_path = LOG_DIR / filename
        file_path.touch(exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_user(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user:
        return None

    return {
        "username": user.get("username"),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role"),
    }


def _safe_request(request_data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not request_data:
        return None

    return {
        "method": request_data.get("method"),
        "path": request_data.get("path"),
        "client_host": request_data.get("client_host"),
        "user_agent": request_data.get("user_agent"),
    }


def write_audit_event(
    *,
    category: str,
    event_type: str,
    result: str,
    user: dict[str, Any] | None = None,
    request_data: dict[str, Any] | None = None,
    resource: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    ensure_log_files()

    if category not in CATEGORY_FILES:
        category = "audit"

    event = {
        "timestamp": _now_iso(),
        "category": category,
        "event_type": event_type,
        "result": result,
        "user": _safe_user(user),
        "request": _safe_request(request_data),
        "resource": resource or {},
        "details": details or {},
    }

    line = json.dumps(event, ensure_ascii=False)

    category_path = LOG_DIR / CATEGORY_FILES[category]
    with category_path.open("a", encoding="utf-8") as file:
        file.write(line + "\n")

    if category != "audit":
        audit_path = LOG_DIR / CATEGORY_FILES["audit"]
        with audit_path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")


def build_request_audit_data(request) -> dict[str, Any]:
    return {
        "method": request.method,
        "path": request.url.path,
        "client_host": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }