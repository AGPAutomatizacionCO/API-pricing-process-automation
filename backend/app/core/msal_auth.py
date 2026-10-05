from functools import lru_cache
from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from app.core.config import get_settings


@lru_cache
def _jwks_client(jwks_uri: str) -> PyJWKClient:
    # PyJWKClient cachea las llaves de firma; no se consulta Entra en cada request.
    return PyJWKClient(jwks_uri, cache_keys=True, lifespan=3600)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _issuers(tenant_id: str) -> list[str]:
    # v2.0 (tokens de app registrations con accessTokenAcceptedVersion=2) y v1.0 (por defecto).
    return [
        f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        f"https://sts.windows.net/{tenant_id}/",
    ]


def validate_bearer_token(token: str, *, signing_key: Any | None = None) -> dict[str, Any]:
    """Valida un access token de Entra ID emitido para esta API y devuelve el usuario.

    `signing_key` solo se usa en pruebas; en ejecucion se obtiene del JWKS del tenant.
    """
    settings = get_settings()

    if not settings.msal_tenant_id or not settings.msal_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MSAL auth is enabled but MSAL_TENANT_ID / MSAL_CLIENT_ID are not set.",
        )

    try:
        if signing_key is None:
            jwks_uri = (
                f"https://login.microsoftonline.com/{settings.msal_tenant_id}/discovery/v2.0/keys"
            )
            signing_key = _jwks_client(jwks_uri).get_signing_key_from_jwt(token).key

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=[
                settings.msal_client_id,
                f"api://{settings.msal_client_id}",
            ],
            options={"require": ["exp", "iss", "aud"]},
            leeway=30,
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token expired.")
    except jwt.PyJWTError:
        # No se detalla el motivo al cliente (firma, audiencia, formato...).
        raise _unauthorized("Invalid token.")

    if claims.get("tid") != settings.msal_tenant_id:
        raise _unauthorized("Invalid token tenant.")
    if claims.get("iss") not in _issuers(settings.msal_tenant_id):
        raise _unauthorized("Invalid token issuer.")

    # Tokens de aplicacion (client credentials) no traen usuario: se rechazan.
    email = claims.get("preferred_username") or claims.get("upn") or claims.get("email")
    if not email:
        raise _unauthorized("Token has no user identity.")

    # Los delegated tokens traen `scp`; se exige el scope configurado.
    required_scope = settings.msal_required_scope
    if required_scope:
        scopes = (claims.get("scp") or "").split()
        if required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token is missing the required scope.",
            )

    return {
        "user_id": claims.get("oid"),
        "email": email.lower(),
        "username": email.lower(),
        "name": claims.get("name") or email,
        "auth_provider": "msal_bearer",
        "app_roles": claims.get("roles") or [],
        "claims": [],
    }
