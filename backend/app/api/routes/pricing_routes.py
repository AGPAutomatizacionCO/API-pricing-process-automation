from typing import Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response

from app.api.dependencies import get_current_user, require_admin, require_analyst, require_viewer
from app.api.schemas import CotizacionCreate, CotizacionIn, EstadoIn, FormulaCreate, FormulaIn
from app.services import pricing_repository as repo

router = APIRouter(prefix="/api/pricing", tags=["pricing"])


def _viewer(request: Request) -> dict:
    user = get_current_user(request)
    require_viewer(user)
    return user


def _analyst(request: Request) -> dict:
    user = get_current_user(request)
    require_analyst(user)
    return user


def _admin(request: Request) -> dict:
    user = get_current_user(request)
    require_admin(user)
    return user


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _run(fn: Callable, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except repo.NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except repo.Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))


def _require_if_match(if_match: str | None) -> str:
    if not if_match:
        raise HTTPException(status_code=428, detail="Falta el header If-Match con el ETag.")
    return if_match.strip('"')


# ── Cotizaciones ──────────────────────────────────────────────

@router.get("/cotizaciones")
def list_cotizaciones(
    estado: str | None = Query(None, pattern="^(abierta|archivada)$"),
    cliente: str | None = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(_viewer),
):
    data = _run(repo.list_cotizaciones, estado=estado, cliente=cliente, limit=limit, offset=offset)
    return {"status": "ok", "count": len(data), "data": data}


@router.get("/cotizaciones/{codigo}")
def get_cotizacion(codigo: str, response: Response, user: dict = Depends(_viewer)):
    data = _run(repo.get_cotizacion, codigo)
    response.headers["ETag"] = f'"{data["etag"]}"'
    return {"status": "ok", "data": data}


@router.post("/cotizaciones", status_code=201)
def create_cotizacion(body: CotizacionCreate, request: Request, user: dict = Depends(_analyst)):
    data = _run(repo.create_cotizacion, body.model_dump(mode="json"), user=user, ip=_ip(request))
    return {"status": "ok", "data": data}


@router.put("/cotizaciones/{codigo}")
def update_cotizacion(codigo: str, body: CotizacionIn, request: Request,
                      if_match: str | None = Header(None), user: dict = Depends(_analyst)):
    data = _run(repo.update_cotizacion, codigo, body.model_dump(mode="json"),
                _require_if_match(if_match), user=user, ip=_ip(request))
    return {"status": "ok", "data": data}


@router.patch("/cotizaciones/{codigo}/estado")
def set_estado(codigo: str, body: EstadoIn, request: Request, user: dict = Depends(_analyst)):
    data = _run(repo.set_estado_cotizacion, codigo, body.estado, user=user, ip=_ip(request))
    return {"status": "ok", "data": data}


@router.delete("/cotizaciones/{codigo}", status_code=204)
def delete_cotizacion(codigo: str, request: Request, user: dict = Depends(_admin)):
    _run(repo.delete_cotizacion, codigo, user=user, ip=_ip(request))
    return Response(status_code=204)


# ── Formulas ──────────────────────────────────────────────────

@router.get("/formulas")
def list_formulas(
    q: str | None = Query(None, max_length=100),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: dict = Depends(_viewer),
):
    data = _run(repo.list_formulas, q=q, limit=limit, offset=offset)
    return {"status": "ok", "count": len(data), "data": data}


@router.get("/formulas/{code}")
def get_formula(code: str, response: Response, user: dict = Depends(_viewer)):
    data = _run(repo.get_formula, code)
    response.headers["ETag"] = f'"{data["etag"]}"'
    return {"status": "ok", "data": data}


@router.post("/formulas", status_code=201)
def create_formula(body: FormulaCreate, request: Request, user: dict = Depends(_admin)):
    data = _run(repo.create_formula, body.model_dump(mode="json"), user=user, ip=_ip(request))
    return {"status": "ok", "data": data}


@router.put("/formulas/{code}")
def update_formula(code: str, body: FormulaIn, request: Request,
                   if_match: str | None = Header(None), user: dict = Depends(_admin)):
    data = _run(repo.update_formula, code, body.model_dump(mode="json"),
                _require_if_match(if_match), user=user, ip=_ip(request))
    return {"status": "ok", "data": data}


@router.delete("/formulas/{code}", status_code=204)
def delete_formula(code: str, request: Request, user: dict = Depends(_admin)):
    _run(repo.delete_formula, code, user=user, ip=_ip(request))
    return Response(status_code=204)
