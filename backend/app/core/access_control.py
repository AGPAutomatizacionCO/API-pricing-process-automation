from fastapi import HTTPException

from app.core.config import get_settings


VALID_ROLES = {
    "ADMIN",
    "ANALYST",
    "VIEWER",
}


ROLE_PRIORITY = {
    "VIEWER": 1,
    "ANALYST": 2,
    "ADMIN": 3,
}


def _parse_user_list(raw_value: str) -> list[str]:
    if not raw_value:
        return []

    return [
        item.strip().lower()
        for item in raw_value.split(",")
        if item.strip()
    ]


def parse_allowed_users() -> dict[str, str]:
    settings = get_settings()

    users: dict[str, str] = {}

    role_sources = [
        ("VIEWER", settings.viewer_users),
        ("ANALYST", settings.analyst_users),
        ("ADMIN", settings.admin_users),
    ]

    for role, raw_users in role_sources:
        for username in _parse_user_list(raw_users):
            current_role = users.get(username)

            if not current_role:
                users[username] = role
                continue

            if ROLE_PRIORITY[role] > ROLE_PRIORITY[current_role]:
                users[username] = role

    return users


def require_user_in_access_list(username: str) -> dict:
    settings = get_settings()

    normalized_username = username.lower().strip()

    if not settings.access_policy_enabled:
        return {
            "username": normalized_username,
            "role": "ADMIN",
        }

    allowed_users = parse_allowed_users()

    if normalized_username not in allowed_users:
        raise HTTPException(
            status_code=403,
            detail="User not authorized",
        )

    return {
        "username": normalized_username,
        "role": allowed_users[normalized_username],
    }


def require_roles(
    session_data: dict,
    allowed_roles: list[str],
) -> None:
    user_role = session_data.get("role")

    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )


def is_admin(session_data: dict) -> bool:
    return session_data.get("role") == "ADMIN"


def is_analyst(session_data: dict) -> bool:
    return session_data.get("role") in {
        "ADMIN",
        "ANALYST",
    }


def is_viewer(session_data: dict) -> bool:
    return session_data.get("role") in {
        "ADMIN",
        "ANALYST",
        "VIEWER",
    }