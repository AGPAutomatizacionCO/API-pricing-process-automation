import pytest
from fastapi.testclient import TestClient

from app.api.routes import db_routes
from app.core import db
from app.core.config import get_settings
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("role,expected", [("VIEWER", 403), ("ANALYST", 403)])
@pytest.mark.parametrize("path", ["/api/db/test", "/api/db/databases", "/api/db/tables"])
def test_db_diagnostics_are_admin_only(monkeypatch, path, role, expected):
    monkeypatch.setattr(db_routes, "get_authenticated_user", lambda request: {"email": "t@agpglass.com"})
    monkeypatch.setattr(db_routes, "require_user_in_access_list", lambda email, roles=None: {"role": role})
    assert client.get(path).status_code == expected


def test_msi_connection_string_has_no_password_and_validates_certificate(monkeypatch):
    s = get_settings()
    for k, v in {"sql_auth_mode": "msi", "sql_msi_client_id": "abc-123", "sql_server": "srv", "sql_database": "db",
                 "sql_password": "NO-DEBE-APARECER", "sql_username": "u"}.items():
        monkeypatch.setattr(s, k, v)
    cs = db.build_connection_string()
    assert "Authentication=ActiveDirectoryMsi" in cs and "UID=abc-123" in cs
    assert "PWD" not in cs and "NO-DEBE-APARECER" not in cs
    assert "TrustServerCertificate=no" in cs


def test_sql_mode_unchanged(monkeypatch):
    s = get_settings()
    for k, v in {"sql_auth_mode": "sql", "sql_trusted_connection": False, "sql_server": "srv", "sql_database": "db",
                 "sql_username": "u", "sql_password": "p"}.items():
        monkeypatch.setattr(s, k, v)
    assert "UID=u;PWD=p;" in db.build_connection_string()
