import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Literal

import requests
from fastapi import HTTPException, Request, Response, status
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import get_settings


_SESSION_STORE: dict[str, dict[str, Any]] = {}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _expires_at() -> datetime:
    settings = get_settings()
    return _now_utc() + timedelta(minutes=settings.session_expire_minutes)


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _cookie_samesite() -> Literal["lax", "strict", "none"]:
    settings = get_settings()
    value = settings.session_cookie_samesite.lower().strip()

    if value in {"lax", "strict", "none"}:
        return value  # type: ignore[return-value]

    return "lax"


@lru_cache(maxsize=1)
def get_microsoft_jwks() -> dict:
    settings = get_settings()

    if not settings.entra_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ENTRA_TENANT_ID is not configured.",
        )

    url = (
        f"https://login.microsoftonline.com/"
        f"{settings.entra_tenant_id}/discovery/v2.0/keys"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()


def validate_microsoft_id_token(id_token: str) -> dict:
    settings = get_settings()

    if not settings.entra_frontend_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ENTRA_FRONTEND_CLIENT_ID is not configured.",
        )

    issuer = settings.get_entra_issuer()

    if not issuer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ENTRA_ISSUER or ENTRA_TENANT_ID is not configured.",
        )

    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Microsoft token header.",
        )

    key_id = header.get("kid")

    if not key_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Microsoft token header does not include kid.",
        )

    signing_key = None

    for key in get_microsoft_jwks().get("keys", []):
        if key.get("kid") == key_id:
            signing_key = key
            break

    if not signing_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Microsoft signing key not found.",
        )

    try:
        claims = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.entra_frontend_client_id,
            issuer=issuer,
            options={
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            },
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Microsoft ID token.",
        )

    token_tenant = claims.get("tid")

    if settings.entra_tenant_id and token_tenant != settings.entra_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Microsoft tenant.",
        )

    return claims


def create_opaque_session(
    *,
    response: Response,
    user: dict[str, Any],
) -> dict[str, Any]:
    settings = get_settings()

    session_id = secrets.token_urlsafe(48)
    expires_at = _expires_at()

    session_data = {
        "session_id": session_id,
        "created_at": _serialize_datetime(_now_utc()),
        "expires_at": _serialize_datetime(expires_at),
        "username": user.get("username"),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role"),
    }

    _SESSION_STORE[session_id] = session_data

    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=_cookie_samesite(),
        max_age=settings.session_expire_minutes * 60,
        path="/",
    )

    return session_data


def get_session_from_request(request: Request) -> dict[str, Any]:
    settings = get_settings()

    session_id = request.cookies.get(settings.session_cookie_name)

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session cookie not found.",
        )

    session_data = _SESSION_STORE.get(session_id)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    expires_at_raw = session_data.get("expires_at")

    if not isinstance(expires_at_raw, str):
        destroy_session_by_id(session_id)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session expiration.",
        )

    try:
        expires_at = datetime.fromisoformat(expires_at_raw)
    except Exception:
        destroy_session_by_id(session_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session expiration.",
        )

    if expires_at <= _now_utc():
        destroy_session_by_id(session_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired.",
        )

    return session_data


def destroy_session_by_id(session_id: str) -> None:
    _SESSION_STORE.pop(session_id, None)


def destroy_session_from_request(
    *,
    request: Request,
    response: Response,
) -> None:
    settings = get_settings()

    session_id = request.cookies.get(settings.session_cookie_name)

    if session_id:
        destroy_session_by_id(session_id)

    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
    )


def public_session_payload(session_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "user": {
            "username": session_data.get("username"),
            "email": session_data.get("email"),
            "name": session_data.get("name"),
            "role": session_data.get("role"),
        },
        "expires_at": session_data.get("expires_at"),
    }