import pytest
from fastapi.testclient import TestClient

from app.api.routes import pricing_routes
from app.main import app
from app.services import pricing_repository as repo

client = TestClient(app)

COT = {
    "codigo": "COT-1",
    "fecha": "2026-10-02",
    "cliente": "ACME",
    "snapshot": {"brief": {}},
}


def as_role(monkeypatch, role):
    monkeypatch.setattr(
        pricing_routes, "get_current_user",
        lambda request: {"email": "t@agpglass.com", "role": role},
    )


@pytest.mark.parametrize("method,url,role,expected", [
    ("get", "/api/pricing/cotizaciones", "VIEWER", 200),
    ("post", "/api/pricing/cotizaciones", "VIEWER", 403),
    ("delete", "/api/pricing/cotizaciones/COT-1", "ANALYST", 403),
    ("post", "/api/pricing/formulas", "ANALYST", 403),
    ("delete", "/api/pricing/formulas/L1", "VIEWER", 403),
])
def test_role_enforcement(monkeypatch, method, url, role, expected):
    as_role(monkeypatch, role)
    monkeypatch.setattr(repo, "list_cotizaciones", lambda **k: [])
    kwargs = {"json": COT} if method == "post" else {}
    assert getattr(client, method)(url, **kwargs).status_code == expected


def test_create_rejects_bad_codigo(monkeypatch):
    as_role(monkeypatch, "ANALYST")
    r = client.post("/api/pricing/cotizaciones", json={**COT, "codigo": "x; DROP TABLE"})
    assert r.status_code == 422


def test_update_requires_if_match(monkeypatch):
    as_role(monkeypatch, "ANALYST")
    body = {k: v for k, v in COT.items() if k != "codigo"}
    assert client.put("/api/pricing/cotizaciones/COT-1", json=body).status_code == 428


def test_update_conflict_maps_to_409(monkeypatch):
    as_role(monkeypatch, "ANALYST")

    def boom(*a, **k):
        raise repo.Conflict("otra persona")

    monkeypatch.setattr(repo, "update_cotizacion", boom)
    body = {k: v for k, v in COT.items() if k != "codigo"}
    r = client.put("/api/pricing/cotizaciones/COT-1", json=body, headers={"If-Match": '"ab"'})
    assert r.status_code == 409


def test_get_not_found_maps_to_404_and_sets_etag(monkeypatch):
    as_role(monkeypatch, "VIEWER")

    def missing(c):
        raise repo.NotFound("no")

    monkeypatch.setattr(repo, "get_cotizacion", missing)
    assert client.get("/api/pricing/cotizaciones/COT-9").status_code == 404

    monkeypatch.setattr(repo, "get_cotizacion", lambda c: {"etag": "0a0b"})
    r = client.get("/api/pricing/cotizaciones/COT-1")
    assert r.headers["ETag"] == '"0a0b"'


def test_estado_only_allows_known_values(monkeypatch):
    as_role(monkeypatch, "ANALYST")
    r = client.patch("/api/pricing/cotizaciones/COT-1/estado", json={"estado": "borrada"})
    assert r.status_code == 422
