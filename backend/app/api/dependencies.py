from fastapi import Request

from app.core.access_control import (
    require_roles,
    require_user_in_access_list,
)
from app.core.easy_auth import get_authenticated_user


def get_current_user(request: Request) -> dict:
    user = get_authenticated_user(request)
    access_user = require_user_in_access_list(user["email"])

    return {
        **user,
        "role": access_user["role"],
    }


def require_admin(user: dict) -> None:
    require_roles(user, ["ADMIN"])


def require_analyst(user: dict) -> None:
    require_roles(user, ["ADMIN", "ANALYST"])


def require_viewer(user: dict) -> None:
    require_roles(user, ["ADMIN", "ANALYST", "VIEWER"])