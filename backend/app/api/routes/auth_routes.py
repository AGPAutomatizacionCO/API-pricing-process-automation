from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.core.access_control import require_user_in_access_list
from app.core.audit_logger import (
    build_request_audit_data,
    write_audit_event,
)
from app.core.session import (
    create_opaque_session,
    destroy_session_from_request,
    get_session_from_request,
    public_session_payload,
)
from app.core.session import validate_microsoft_id_token


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


class AuthSessionRequest(BaseModel):
    id_token: str


@router.post("/session")
def create_session(
    payload: AuthSessionRequest,
    request: Request,
    response: Response,
):
    try:
        claims = validate_microsoft_id_token(payload.id_token)

        username = (
            claims.get("preferred_username")
            or claims.get("email")
            or claims.get("upn")
        )

        if not username:
            raise HTTPException(
                status_code=401,
                detail="Username not found in token.",
            )

        access_user = require_user_in_access_list(username)

        user = {
            "username": username.lower(),
            "email": username.lower(),
            "name": claims.get("name"),
            "role": access_user["role"],
        }

        session_data = create_opaque_session(
            response=response,
            user=user,
        )

        write_audit_event(
            category="auth",
            event_type="SESSION_CREATED",
            result="SUCCESS",
            user=user,
            request_data=build_request_audit_data(request),
            resource={
                "resource_type": "auth_session",
            },
            details={
                "message": "Backend session created.",
            },
        )

        return {
            "status": "ok",
            "session": public_session_payload(session_data),
        }

    except HTTPException as exc:
        event_category = "access_denied" if exc.status_code in [401, 403] else "errors"

        write_audit_event(
            category=event_category,
            event_type="SESSION_CREATE_BLOCKED",
            result="FAILED",
            user=None,
            request_data=build_request_audit_data(request),
            resource={
                "resource_type": "auth_session",
            },
            details={
                "status_code": exc.status_code,
                "message": exc.detail,
            },
        )

        raise exc

    except Exception as exc:
        write_audit_event(
            category="errors",
            event_type="SESSION_CREATE_ERROR",
            result="FAILED",
            user=None,
            request_data=build_request_audit_data(request),
            resource={
                "resource_type": "auth_session",
            },
            details={
                "message": str(exc),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Unexpected authentication error.",
        )


@router.get("/me")
def get_current_user(request: Request):
    session = get_session_from_request(request)

    return {
        "status": "ok",
        "session": public_session_payload(session),
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
):
    session = None

    try:
        session = get_session_from_request(request)
    except Exception:
        session = None

    destroy_session_from_request(
        request=request,
        response=response,
    )

    write_audit_event(
        category="auth",
        event_type="SESSION_CLOSED",
        result="SUCCESS",
        user=session,
        request_data=build_request_audit_data(request),
        resource={
            "resource_type": "auth_session",
        },
        details={
            "message": "Backend session closed.",
        },
    )

    return {
        "status": "ok",
        "message": "Session closed",
    }


@router.get("/test-protected")
def test_protected(request: Request):
    session = get_session_from_request(request)

    return {
        "status": "ok",
        "user": {
            "username": session.get("username"),
            "email": session.get("email"),
            "name": session.get("name"),
            "role": session.get("role"),
        },
    }