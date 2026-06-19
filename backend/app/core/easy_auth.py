import base64
import json
from typing import Any

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


def _decode_easy_auth_principal(raw_value: str) -> dict[str, Any]:
    try:
        decoded_bytes = base64.b64decode(raw_value)
        decoded_text = decoded_bytes.decode("utf-8")
        return json.loads(decoded_text)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Easy Auth principal header.",
        )


def _get_claim(principal: dict[str, Any], claim_type: str) -> str | None:
    claims = principal.get("claims") or []

    for claim in claims:
        if claim.get("typ") == claim_type:
            value = claim.get("val")
            return str(value) if value else None

    return None


def get_authenticated_user(request: Request) -> dict[str, Any]:
    settings = get_settings()

    principal_raw = request.headers.get("x-ms-client-principal")

    if principal_raw:
        principal = _decode_easy_auth_principal(principal_raw)

        email = (
            _get_claim(principal, "preferred_username")
            or _get_claim(principal, "email")
            or request.headers.get("x-ms-client-principal-name")
        )

        name = (
            _get_claim(principal, "name")
            or request.headers.get("x-ms-client-principal-name")
            or email
        )

        user_id = request.headers.get("x-ms-client-principal-id")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user email not found.",
            )

        return {
            "user_id": user_id,
            "email": email.lower(),
            "username": email.lower(),
            "name": name,
            "auth_provider": "azure_easy_auth",
            "claims": principal.get("claims") or [],
        }

    if settings.app_env == "local" and settings.local_auth_enabled:
        return {
            "user_id": "local-dev-user",
            "email": settings.local_auth_email.lower(),
            "username": settings.local_auth_email.lower(),
            "name": settings.local_auth_name,
            "auth_provider": "local_dev",
            "claims": [],
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
    )