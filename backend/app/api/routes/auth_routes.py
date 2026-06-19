from fastapi import APIRouter, HTTPException, Request

from app.core.access_control import require_user_in_access_list
from app.core.audit_logger import (
    build_request_audit_data,
    write_audit_event,
)
from app.core.easy_auth import get_authenticated_user


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.get("/me")
def get_current_user(request: Request):
    try:
        user = get_authenticated_user(request)
        access_user = require_user_in_access_list(user["email"])

        response_user = {
            "username": user["email"],
            "email": user["email"],
            "name": user.get("name"),
            "role": access_user["role"],
            "auth_provider": user.get("auth_provider"),
        }

        write_audit_event(
            category="auth",
            event_type="AUTH_ME_ACCESSED",
            result="SUCCESS",
            user=response_user,
            request_data=build_request_audit_data(request),
            resource={
                "resource_type": "auth_user",
                "resource_name": "/auth/me",
            },
            details={
                "message": "Authenticated user resolved from Easy Auth.",
            },
        )

        return {
            "status": "ok",
            "user": response_user,
        }

    except HTTPException as exc:
        write_audit_event(
            category="access_denied",
            event_type="AUTH_ME_DENIED",
            result="FAILED",
            user=None,
            request_data=build_request_audit_data(request),
            resource={
                "resource_type": "auth_user",
                "resource_name": "/auth/me",
            },
            details={
                "status_code": exc.status_code,
                "message": exc.detail,
            },
        )

        raise exc


@router.get("/test-protected")
def test_protected(request: Request):
    user = get_authenticated_user(request)
    access_user = require_user_in_access_list(user["email"])

    return {
        "status": "ok",
        "user": {
            "username": user["email"],
            "email": user["email"],
            "name": user.get("name"),
            "role": access_user["role"],
            "auth_provider": user.get("auth_provider"),
        },
    }