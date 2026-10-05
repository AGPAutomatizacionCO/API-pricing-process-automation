from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


class PiezaIn(BaseModel):
    part_no: str | None = Field(None, max_length=100)
    descripcion: str | None = Field(None, max_length=300)
    superficie: str | None = Field(None, max_length=50)
    ancho_mm: float | None = Field(None, ge=0)
    alto_mm: float | None = Field(None, ge=0)
    piezas: int = Field(1, ge=1)
    sets: int = Field(1, ge=1)
    formula_code: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=100)
    bb: str | None = Field(None, max_length=100)
    feat: str | None = Field(None, max_length=300)


class CotizacionIn(BaseModel):
    fecha: date
    unidad_comercial: str | None = Field(None, max_length=200)
    cliente: str | None = Field(None, max_length=200)
    pm: str | None = Field(None, max_length=200)
    programa: str | None = Field(None, max_length=200)
    precio_min_aprobado: float | None = Field(None, ge=0)
    precio_target: float | None = Field(None, ge=0)
    piezas: list[PiezaIn] = Field(default_factory=list, max_length=50)
    snapshot: dict[str, Any]


class CotizacionCreate(CotizacionIn):
    codigo: str = Field(..., pattern=r"^COT-[0-9A-Za-z_-]{1,35}$")


class EstadoIn(BaseModel):
    estado: Literal["abierta", "archivada"]


class FormulaIn(BaseModel):
    nombre: str | None = Field(None, max_length=300)
    nivel: str | None = Field(None, max_length=10)
    geo: str | None = Field(None, max_length=50)
    tipo_prod: str | None = Field(None, max_length=100)
    area: float | None = Field(None, ge=0)
    espesor_mm: float | None = Field(None, ge=0)
    rech_pct: float | None = Field(None, ge=0, le=1)
    empq_m2: float | None = None
    pint_m2: float | None = None
    teco_m2: float | None = None
    costo_total: float | None = None
    detalle: dict[str, Any]


class FormulaCreate(FormulaIn):
    code: str = Field(..., min_length=1, max_length=50)
