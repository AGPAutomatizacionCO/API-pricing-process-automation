from fastapi import Request

from app.core.access_control import require_roles
from app.core.session import get_session_from_request


def get_current_session(request: Request) -> dict:
    return get_session_from_request(request)


def require_admin(session: dict) -> None:
    require_roles(session, ["ADMIN"])


def require_analyst(session: dict) -> None:
    require_roles(session, ["ADMIN", "ANALYST"])


def require_viewer(session: dict) -> None:
    require_roles(
        session,
        [
            "ADMIN",
            "ANALYST",
            "VIEWER",
        ],
    )