import base64
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core import msal_auth
from app.core.config import get_settings
from app.main import app

TENANT = "11111111-1111-1111-1111-111111111111"
API = "22222222-2222-2222-2222-222222222222"

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)

client = TestClient(app)


@pytest.fixture(autouse=True)
def msal_settings(monkeypatch):
    s = get_settings()
    for k, v in {
        "msal_auth_enabled": True, "msal_tenant_id": TENANT, "msal_client_id": API,
        "msal_required_scope": "access_as_user", "easy_auth_enabled": True,
        "app_env": "azure", "local_auth_enabled": False, "access_policy_enabled": True,
        "admin_users": "", "analyst_users": "", "viewer_users": "",
    }.items():
        monkeypatch.setattr(s, k, v)
    # En pruebas la llave de firma sale de KEY, no del JWKS de Entra.
    monkeypatch.setattr(
        msal_auth, "_jwks_client",
        lambda uri: type("C", (), {"get_signing_key_from_jwt": lambda self, t: type("K", (), {"key": KEY.public_key()})()})(),
    )


def token(key=KEY, **over):
    claims = {
        "aud": API, "iss": f"https://login.microsoftonline.com/{TENANT}/v2.0", "tid": TENANT,
        "exp": int(time.time()) + 600, "iat": int(time.time()),
        "preferred_username": "Ana@agpglass.com", "name": "Ana", "oid": "abc",
        "scp": "access_as_user", "roles": ["Pricing.Analyst"],
    }
    claims.update(over)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm="RS256")


def me(tok):
    return client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})


def test_valid_token_gets_role_from_app_role():
    r = me(token())
    assert r.status_code == 200
    assert "ANALYST" in json.dumps(r.json())
    assert "ana@agpglass.com" in json.dumps(r.json())


def test_highest_app_role_wins():
    r = me(token(roles=["Pricing.Viewer", "Pricing.Admin"]))
    assert r.status_code == 200 and "ADMIN" in json.dumps(r.json())


@pytest.mark.parametrize("over,status", [
    ({"exp": int(time.time()) - 3600}, 401),
    ({"aud": "otra-api"}, 401),
    ({"tid": "otro-tenant"}, 401),
    ({"iss": "https://evil.example/"}, 401),
    ({"preferred_username": None, "upn": None, "email": None}, 401),
    ({"scp": "otro"}, 403),
    ({"roles": []}, 403),
    ({"roles": ["Otra.Cosa"]}, 403),
])
def test_rejections(over, status):
    assert me(token(**over)).status_code == status


def test_token_signed_with_other_key_is_rejected():
    assert me(token(key=OTHER)).status_code == 401


def test_garbage_token_is_401_and_does_not_fall_back():
    assert me("no-es-un-jwt").status_code == 401


def test_forged_easy_auth_header_ignored_when_easy_auth_disabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "easy_auth_enabled", False)
    principal = base64.b64encode(json.dumps(
        {"claims": [{"typ": "preferred_username", "val": "admin@agpglass.com"}]}).encode()).decode()
    r = client.get("/auth/me", headers={"x-ms-client-principal": principal})
    assert r.status_code == 401


def test_easy_auth_path_still_works_with_access_list(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "viewer_users", "ana@agpglass.com")
    principal = base64.b64encode(json.dumps(
        {"claims": [{"typ": "preferred_username", "val": "ana@agpglass.com"}]}).encode()).decode()
    r = client.get("/auth/me", headers={"x-ms-client-principal": principal})
    assert r.status_code == 200 and "VIEWER" in json.dumps(r.json())
