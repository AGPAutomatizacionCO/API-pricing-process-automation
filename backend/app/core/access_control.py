from fastapi import HTTPException, status

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


def _parse_csv(raw_value: str) -> list[str]:
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
        for email in _parse_csv(raw_users):
            current_role = users.get(email)

            if not current_role:
                users[email] = role
                continue

            if ROLE_PRIORITY[role] > ROLE_PRIORITY[current_role]:
                users[email] = role

    return users


def require_user_in_access_list(email: str) -> dict:
    settings = get_settings()
    normalized_email = email.lower().strip()

    if not settings.access_policy_enabled:
        return {
            "email": normalized_email,
            "username": normalized_email,
            "role": "ADMIN",
        }

    allowed_users = parse_allowed_users()

    if normalized_email not in allowed_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized.",
        )

    return {
        "email": normalized_email,
        "username": normalized_email,
        "role": allowed_users[normalized_email],
    }


def require_roles(
    user: dict,
    allowed_roles: list[str],
) -> None:
    user_role = user.get("role")

    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )


def is_admin(user: dict) -> bool:
    return user.get("role") == "ADMIN"


def is_analyst(user: dict) -> bool:
    return user.get("role") in {
        "ADMIN",
        "ANALYST",
    }


def is_viewer(user: dict) -> bool:
    return user.get("role") in {
        "ADMIN",
        "ANALYST",
        "VIEWER",
    }