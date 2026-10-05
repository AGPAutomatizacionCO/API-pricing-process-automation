"""Mapeo de los datos legados del frontend HTML a los payloads del CRUD.

- formula_library.json  -> dbo.App_Finanzas_Pricing_Formula
- export de localStorage 'agp_cotizaciones_v1' -> dbo.App_Finanzas_Pricing_Cotizacion (+ _pieza)
"""
import re
from datetime import datetime
from typing import Any

from app.api.schemas import CotizacionCreate, FormulaCreate

# Campos de la formula que tienen columna propia; el resto va a DetalleJson.
_FORMULA_COLUMNS = {
    "code": "code", "nombre": "nombre", "nivel": "nivel", "geo": "geo",
    "tipoProd": "tipo_prod", "area": "area", "espesorMm": "espesor_mm",
    "rechPct": "rech_pct", "empqM2": "empq_m2", "pintM2": "pint_m2",
    "tecoM2": "teco_m2", "costoTotal": "costo_total",
}


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _int(value: Any, default: int = 1) -> int:
    n = _num(value)
    return max(int(n), 1) if n is not None else default


def _str(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def map_formula(legacy: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for src, dst in _FORMULA_COLUMNS.items():
        value = legacy.get(src)
        payload[dst] = _str(value) if dst in {"code", "nombre", "nivel", "geo", "tipo_prod"} else _num(value)
    payload["detalle"] = {k: v for k, v in legacy.items() if k not in _FORMULA_COLUMNS}
    FormulaCreate(**payload)  # valida; lanza ValidationError si no cumple el contrato
    return payload


def map_cotizacion(legacy: dict[str, Any]) -> dict[str, Any]:
    snap = legacy.get("snapshot") or {}
    codigo = _str(legacy.get("id")) or ""
    # El contrato exige COT-<alfanumerico>; los ids del HTML son 'COT-<timestamp>'.
    codigo = re.sub(r"[^0-9A-Za-z_-]", "", codigo.removeprefix("COT-"))
    payload = {
        "codigo": f"COT-{codigo}",
        "fecha": _str(legacy.get("fecha")) or (_str(legacy.get("savedAt")) or "")[:10],
        "unidad_comercial": _str(legacy.get("unit")),
        "cliente": _str(legacy.get("cli")),
        "pm": _str(legacy.get("pm")),
        "programa": _str(legacy.get("prog")),
        "precio_min_aprobado": _num(snap.get("precioMinAprobado")),
        "precio_target": _num(snap.get("precioTarget")),
        "piezas": [
            {
                "part_no": _str(p.get("partno")), "descripcion": _str(p.get("desc")),
                "superficie": _str(p.get("surf")), "ancho_mm": _num(p.get("w")),
                "alto_mm": _num(p.get("h")), "piezas": _int(p.get("pcs")),
                "sets": _int(p.get("sets")), "formula_code": _str(p.get("formula")),
                "color": _str(p.get("color")), "bb": _str(p.get("bb")), "feat": _str(p.get("feat")),
            }
            for p in (snap.get("briefPieces") or [])
        ],
        # Se conserva el registro original completo para no perder nada del legado.
        "snapshot": {**snap, "_legacy": {"id": legacy.get("id"), "savedAt": legacy.get("savedAt")}},
    }
    CotizacionCreate(**payload)
    return payload


def legacy_estado(legacy: dict[str, Any]) -> str:
    return "archivada" if legacy.get("estado") == "archivada" else "abierta"


_SAVED_AT = re.compile(
    r"(\d{1,2})/(\d{1,2})/(\d{4}),?\s+(\d{1,2}):(\d{2}):(\d{2})\s*([ap])\.?\s*m\.?", re.I
)


def parse_saved_at(value: Any) -> datetime:
    """Fecha de guardado del HTML. Formato es-CO: '29/7/2026, 2:08:32 p. m.'; tambien ISO."""
    text = str(value or "")
    m = _SAVED_AT.search(text)
    if m:
        d, mo, y, h, mi, se, ap = m.groups()
        hour = int(h) % 12 + (12 if ap.lower() == "p" else 0)
        return datetime(int(y), int(mo), int(d), hour, int(mi), int(se))
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def pick_latest_formulas(items: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    """El codigo no es unico en el legado (cada guardado agrega una version).

    Devuelve (vigentes, reemplazadas): la mas reciente por codigo (sin distinguir
    mayusculas, igual que el indice unico de SQL) y las versiones anteriores.
    """
    groups: dict[str, list[dict]] = {}
    for item in items:
        groups.setdefault(str(item.get("code") or "").strip().lower(), []).append(item)
    kept, superseded = [], []
    for versions in groups.values():
        ordered = sorted(versions, key=lambda v: parse_saved_at(v.get("savedAt")), reverse=True)
        kept.append(ordered[0])
        superseded.extend(ordered[1:])
    return kept, superseded
