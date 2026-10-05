import json
from typing import Any

from app.core.db import get_connection


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


def _etag(raw: bytes) -> str:
    return raw.hex()


def _from_etag(etag: str) -> bytes:
    try:
        return bytes.fromhex(etag)
    except ValueError:
        raise Conflict("ETag invalido.")


def _write_audit(cursor, *, user: dict, evento: str, entidad: str,
                 entidad_id: str | None, resultado: str = "SUCCESS",
                 ip: str | None = None, detalle: dict | None = None) -> None:
    cursor.execute(
        """
        INSERT INTO dbo.App_Finanzas_Pricing_Auditoria
            (UsuarioEmail, Rol, Evento, Entidad, EntidadId, Resultado, Ip, DetalleJson)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        user["email"], user.get("role"), evento, entidad, entidad_id, resultado, ip,
        json.dumps(detalle, ensure_ascii=False) if detalle else None,
    )


# ───────────────────────── Cotizaciones ─────────────────────────

_COT_COLS = """
    IdCotizacion, Codigo, Fecha, UnidadComercial, Cliente, Pm, Programa, Estado,
    PrecioMinAprobado, PrecioTarget, CreadoPor, CreadoEnUtc, ModificadoPor, ModificadoEnUtc, RowVer
"""


def _cot_row(row, with_snapshot: bool = False) -> dict[str, Any]:
    data = {
        "id": row.IdCotizacion,
        "codigo": row.Codigo,
        "fecha": row.Fecha.isoformat(),
        "unidad_comercial": row.UnidadComercial,
        "cliente": row.Cliente,
        "pm": row.Pm,
        "programa": row.Programa,
        "estado": row.Estado,
        "precio_min_aprobado": float(row.PrecioMinAprobado) if row.PrecioMinAprobado is not None else None,
        "precio_target": float(row.PrecioTarget) if row.PrecioTarget is not None else None,
        "creado_por": row.CreadoPor,
        "creado_en": row.CreadoEnUtc.isoformat(),
        "modificado_por": row.ModificadoPor,
        "modificado_en": row.ModificadoEnUtc.isoformat() if row.ModificadoEnUtc else None,
        "etag": _etag(row.RowVer),
    }
    if with_snapshot:
        data["snapshot"] = json.loads(row.SnapshotJson)
    return data


def _replace_piezas(cursor, cotizacion_id: int, piezas: list[dict]) -> None:
    cursor.execute("DELETE FROM dbo.App_Finanzas_Pricing_CotizacionPieza WHERE IdCotizacion = ?", cotizacion_id)
    for i, p in enumerate(piezas, start=1):
        cursor.execute(
            """
            INSERT INTO dbo.App_Finanzas_Pricing_CotizacionPieza
                (IdCotizacion, Linea, PartNo, Descripcion, Superficie, AnchoMm, AltoMm,
                 Piezas, Sets, FormulaCode, Color, Bb, Feat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            cotizacion_id, i, p.get("part_no"), p.get("descripcion"), p.get("superficie"),
            p.get("ancho_mm"), p.get("alto_mm"), p.get("piezas", 1), p.get("sets", 1),
            p.get("formula_code"), p.get("color"), p.get("bb"), p.get("feat"),
        )


def list_cotizaciones(*, estado: str | None, cliente: str | None,
                      limit: int, offset: int) -> list[dict]:
    query = f"""
        SELECT {_COT_COLS}
        FROM dbo.App_Finanzas_Pricing_Cotizacion
        WHERE Eliminada = 0
          AND (? IS NULL OR Estado = ?)
          AND (? IS NULL OR Cliente LIKE ?)
        ORDER BY Fecha DESC, IdCotizacion DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    like = f"%{cliente}%" if cliente else None
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, estado, estado, cliente, like, offset, limit)
        return [_cot_row(r) for r in cur.fetchall()]


def get_cotizacion(codigo: str) -> dict:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT {_COT_COLS}, SnapshotJson FROM dbo.App_Finanzas_Pricing_Cotizacion "
            "WHERE Codigo = ? AND Eliminada = 0",
            codigo,
        )
        row = cur.fetchone()
        if not row:
            raise NotFound("Cotizacion no encontrada.")
        data = _cot_row(row, with_snapshot=True)
        cur.execute(
            """
            SELECT Linea, PartNo, Descripcion, Superficie, AnchoMm, AltoMm, Piezas, Sets,
                   FormulaCode, Color, Bb, Feat
            FROM dbo.App_Finanzas_Pricing_CotizacionPieza WHERE IdCotizacion = ? ORDER BY Linea
            """,
            row.IdCotizacion,
        )
        data["piezas"] = [
            {
                "linea": r.Linea, "part_no": r.PartNo, "descripcion": r.Descripcion,
                "superficie": r.Superficie,
                "ancho_mm": float(r.AnchoMm) if r.AnchoMm is not None else None,
                "alto_mm": float(r.AltoMm) if r.AltoMm is not None else None,
                "piezas": r.Piezas, "sets": r.Sets, "formula_code": r.FormulaCode,
                "color": r.Color, "bb": r.Bb, "feat": r.Feat,
            }
            for r in cur.fetchall()
        ]
        return data


def create_cotizacion(payload: dict, *, user: dict, ip: str | None) -> dict:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO dbo.App_Finanzas_Pricing_Cotizacion
                (Codigo, Fecha, UnidadComercial, Cliente, Pm, Programa, Estado,
                 PrecioMinAprobado, PrecioTarget, SnapshotJson, CreadoPor)
            OUTPUT INSERTED.IdCotizacion
            VALUES (?, ?, ?, ?, ?, ?, 'abierta', ?, ?, ?, ?)
            """,
            payload["codigo"], payload["fecha"], payload.get("unidad_comercial"),
            payload.get("cliente"), payload.get("pm"), payload.get("programa"),
            payload.get("precio_min_aprobado"), payload.get("precio_target"),
            json.dumps(payload["snapshot"], ensure_ascii=False), user["email"],
        )
        cot_id = cur.fetchone()[0]
        _replace_piezas(cur, cot_id, payload.get("piezas", []))
        _write_audit(cur, user=user, evento="COTIZACION_CREADA", entidad="Cotizacion",
                     entidad_id=payload["codigo"], ip=ip)
        conn.commit()
    return get_cotizacion(payload["codigo"])


def update_cotizacion(codigo: str, payload: dict, etag: str, *, user: dict, ip: str | None) -> dict:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.App_Finanzas_Pricing_Cotizacion
               SET Fecha = ?, UnidadComercial = ?, Cliente = ?, Pm = ?, Programa = ?,
                   PrecioMinAprobado = ?, PrecioTarget = ?, SnapshotJson = ?,
                   ModificadoPor = ?, ModificadoEnUtc = SYSUTCDATETIME()
            OUTPUT INSERTED.IdCotizacion
             WHERE Codigo = ? AND Eliminada = 0 AND RowVer = ?
            """,
            payload["fecha"], payload.get("unidad_comercial"), payload.get("cliente"),
            payload.get("pm"), payload.get("programa"), payload.get("precio_min_aprobado"),
            payload.get("precio_target"), json.dumps(payload["snapshot"], ensure_ascii=False),
            user["email"], codigo, _from_etag(etag),
        )
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT 1 FROM dbo.App_Finanzas_Pricing_Cotizacion WHERE Codigo = ? AND Eliminada = 0", codigo)
            if not cur.fetchone():
                raise NotFound("Cotizacion no encontrada.")
            raise Conflict("La cotizacion fue modificada por otra persona. Recarga y reintenta.")
        _replace_piezas(cur, row[0], payload.get("piezas", []))
        _write_audit(cur, user=user, evento="COTIZACION_ACTUALIZADA", entidad="Cotizacion",
                     entidad_id=codigo, ip=ip)
        conn.commit()
    return get_cotizacion(codigo)


def set_estado_cotizacion(codigo: str, estado: str, *, user: dict, ip: str | None) -> dict:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.App_Finanzas_Pricing_Cotizacion
               SET Estado = ?, ModificadoPor = ?, ModificadoEnUtc = SYSUTCDATETIME()
             WHERE Codigo = ? AND Eliminada = 0
            """,
            estado, user["email"], codigo,
        )
        if cur.rowcount == 0:
            raise NotFound("Cotizacion no encontrada.")
        _write_audit(cur, user=user, evento="COTIZACION_ESTADO", entidad="Cotizacion",
                     entidad_id=codigo, ip=ip, detalle={"estado": estado})
        conn.commit()
    return get_cotizacion(codigo)


def delete_cotizacion(codigo: str, *, user: dict, ip: str | None) -> None:
    """Borrado logico: la fila se conserva para auditoria."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.App_Finanzas_Pricing_Cotizacion
               SET Eliminada = 1, ModificadoPor = ?, ModificadoEnUtc = SYSUTCDATETIME()
             WHERE Codigo = ? AND Eliminada = 0
            """,
            user["email"], codigo,
        )
        if cur.rowcount == 0:
            raise NotFound("Cotizacion no encontrada.")
        _write_audit(cur, user=user, evento="COTIZACION_ELIMINADA", entidad="Cotizacion",
                     entidad_id=codigo, ip=ip)
        conn.commit()


# ───────────────────────── Formulas ─────────────────────────

_FM_COLS = """
    IdFormula, Code, Nombre, Nivel, Geo, TipoProd, Area, EspesorMm, RechPct,
    EmpqM2, PintM2, TecoM2, CostoTotal, CreadoPor, CreadoEnUtc, ModificadoPor,
    ModificadoEnUtc, RowVer
"""


def _num(v):
    return float(v) if v is not None else None


def _fm_row(row, with_detail: bool = False) -> dict[str, Any]:
    data = {
        "id": row.IdFormula, "code": row.Code, "nombre": row.Nombre, "nivel": row.Nivel,
        "geo": row.Geo, "tipo_prod": row.TipoProd, "area": _num(row.Area),
        "espesor_mm": _num(row.EspesorMm), "rech_pct": _num(row.RechPct),
        "empq_m2": _num(row.EmpqM2), "pint_m2": _num(row.PintM2), "teco_m2": _num(row.TecoM2),
        "costo_total": _num(row.CostoTotal), "creado_por": row.CreadoPor,
        "creado_en": row.CreadoEnUtc.isoformat(), "modificado_por": row.ModificadoPor,
        "modificado_en": row.ModificadoEnUtc.isoformat() if row.ModificadoEnUtc else None,
        "etag": _etag(row.RowVer),
    }
    if with_detail:
        data["detalle"] = json.loads(row.DetalleJson)
    return data


def _fm_params(p: dict) -> tuple:
    return (
        p.get("nombre"), p.get("nivel"), p.get("geo"), p.get("tipo_prod"), p.get("area"),
        p.get("espesor_mm"), p.get("rech_pct"), p.get("empq_m2"), p.get("pint_m2"),
        p.get("teco_m2"), p.get("costo_total"), json.dumps(p["detalle"], ensure_ascii=False),
    )


def list_formulas(*, q: str | None, limit: int, offset: int) -> list[dict]:
    like = f"%{q}%" if q else None
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT {_FM_COLS} FROM dbo.App_Finanzas_Pricing_Formula
            WHERE Eliminada = 0 AND (? IS NULL OR Code LIKE ? OR Nombre LIKE ?)
            ORDER BY Code
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            q, like, like, offset, limit,
        )
        return [_fm_row(r) for r in cur.fetchall()]


def get_formula(code: str) -> dict:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT {_FM_COLS}, DetalleJson FROM dbo.App_Finanzas_Pricing_Formula WHERE Code = ? AND Eliminada = 0",
            code,
        )
        row = cur.fetchone()
        if not row:
            raise NotFound("Formula no encontrada.")
        return _fm_row(row, with_detail=True)


def create_formula(payload: dict, *, user: dict, ip: str | None) -> dict:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.App_Finanzas_Pricing_Formula WHERE Code = ? AND Eliminada = 0", payload["code"])
        if cur.fetchone():
            raise Conflict("Ya existe una formula con ese codigo.")
        cur.execute(
            """
            INSERT INTO dbo.App_Finanzas_Pricing_Formula
                (Code, Nombre, Nivel, Geo, TipoProd, Area, EspesorMm, RechPct,
                 EmpqM2, PintM2, TecoM2, CostoTotal, DetalleJson, CreadoPor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload["code"], *_fm_params(payload), user["email"],
        )
        _write_audit(cur, user=user, evento="FORMULA_CREADA", entidad="Formula",
                     entidad_id=payload["code"], ip=ip)
        conn.commit()
    return get_formula(payload["code"])


def update_formula(code: str, payload: dict, etag: str, *, user: dict, ip: str | None) -> dict:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.App_Finanzas_Pricing_Formula
               SET Nombre = ?, Nivel = ?, Geo = ?, TipoProd = ?, Area = ?, EspesorMm = ?,
                   RechPct = ?, EmpqM2 = ?, PintM2 = ?, TecoM2 = ?, CostoTotal = ?,
                   DetalleJson = ?, ModificadoPor = ?, ModificadoEnUtc = SYSUTCDATETIME()
             WHERE Code = ? AND Eliminada = 0 AND RowVer = ?
            """,
            *_fm_params(payload), user["email"], code, _from_etag(etag),
        )
        if cur.rowcount == 0:
            cur.execute("SELECT 1 FROM dbo.App_Finanzas_Pricing_Formula WHERE Code = ? AND Eliminada = 0", code)
            if not cur.fetchone():
                raise NotFound("Formula no encontrada.")
            raise Conflict("La formula fue modificada por otra persona. Recarga y reintenta.")
        _write_audit(cur, user=user, evento="FORMULA_ACTUALIZADA", entidad="Formula",
                     entidad_id=code, ip=ip)
        conn.commit()
    return get_formula(code)


def delete_formula(code: str, *, user: dict, ip: str | None) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.App_Finanzas_Pricing_Formula
               SET Eliminada = 1, ModificadoPor = ?, ModificadoEnUtc = SYSUTCDATETIME()
             WHERE Code = ? AND Eliminada = 0
            """,
            user["email"], code,
        )
        if cur.rowcount == 0:
            raise NotFound("Formula no encontrada.")
        _write_audit(cur, user=user, evento="FORMULA_ELIMINADA", entidad="Formula",
                     entidad_id=code, ip=ip)
        conn.commit()
