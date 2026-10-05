from datetime import datetime

import pytest
from pydantic import ValidationError

from app.services import legacy_migration as lm


def test_parse_saved_at_spanish_locale():
    assert lm.parse_saved_at("29/7/2026, 2:08:32 p. m.") == datetime(2026, 7, 29, 14, 8, 32)
    assert lm.parse_saved_at("29/7/2026, 12:05:00 a. m.") == datetime(2026, 7, 29, 0, 5, 0)
    assert lm.parse_saved_at("29/7/2026, 12:05:00 p. m.") == datetime(2026, 7, 29, 12, 5, 0)
    assert lm.parse_saved_at("2026-07-29T10:00:00Z") == datetime(2026, 7, 29, 10, 0, 0)
    assert lm.parse_saved_at("basura") == datetime.min


def test_latest_version_wins_case_insensitive_and_nothing_lost():
    items = [
        {"code": "L21-1", "savedAt": "29/7/2026, 8:07:54 a. m.", "costoTotal": 186},
        {"code": "l21-1", "savedAt": "27/8/2026, 3:25:46 p. m.", "costoTotal": 337},
        {"code": "L21-1", "savedAt": "29/7/2026, 2:08:32 p. m.", "costoTotal": 206},
        {"code": "L99-9", "savedAt": "1/1/2026, 1:00:00 a. m."},
    ]
    kept, superseded = lm.pick_latest_formulas(items)
    assert len(kept) + len(superseded) == len(items)
    assert {k["costoTotal"] for k in kept if k["code"].lower() == "l21-1"} == {337}
    assert sorted(s["costoTotal"] for s in superseded) == [186, 206]


def test_map_formula_splits_columns_and_detail():
    p = lm.map_formula({"code": " L1 ", "nivel": "3", "area": "0,5357", "rechPct": 0.1,
                        "rows": [{"item": 1}], "savedAt": "x"})
    assert p["code"] == "L1" and p["area"] == 0.5357 and p["nivel"] == "3"
    assert p["detalle"] == {"rows": [{"item": 1}], "savedAt": "x"}


def test_map_formula_rejects_out_of_range():
    with pytest.raises(ValidationError):
        lm.map_formula({"code": "L1", "rechPct": 5})


def test_map_cotizacion():
    legacy = {
        "id": "COT-1727800000000", "fecha": "2026-10-01", "unit": "Aut", "cli": "ACME", "pm": "Ana",
        "prog": "P1", "estado": "archivada", "savedAt": "2026-10-01T10:00:00Z",
        "snapshot": {"precioMinAprobado": 12.5, "precioTarget": "15",
                     "briefPieces": [{"partno": "A1", "w": "1200", "h": "", "pcs": "2", "sets": "", "formula": "L1"}]},
    }
    p = lm.map_cotizacion(legacy)
    assert p["codigo"] == "COT-1727800000000" and p["cliente"] == "ACME"
    assert p["precio_target"] == 15.0 and p["precio_min_aprobado"] == 12.5
    pz = p["piezas"][0]
    assert (pz["ancho_mm"], pz["alto_mm"], pz["piezas"], pz["sets"]) == (1200.0, None, 2, 1)
    assert p["snapshot"]["_legacy"]["id"] == "COT-1727800000000"
    assert lm.legacy_estado(legacy) == "archivada"


def test_map_cotizacion_rejects_missing_fecha():
    with pytest.raises(ValidationError):
        lm.map_cotizacion({"id": "COT-1", "snapshot": {}})
