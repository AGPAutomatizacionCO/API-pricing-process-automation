"""Migra formulas y cotizaciones del frontend HTML a las tablas pricing.*

Uso (desde backend/):
  python -m scripts.migrate_legacy --formulas ../../pricing-process-automation/formula_library.json
  python -m scripts.migrate_legacy --cotizaciones cotizaciones_export.json
  ... agregar --apply para escribir en la base (por defecto es DRY-RUN y no se conecta).

El export de cotizaciones se obtiene en la consola del navegador de cada usuario:
  copy(localStorage.getItem('agp_cotizaciones_v1'))   y se pega en un .json
Es idempotente: lo que ya existe se omite.
"""
import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from app.services import legacy_migration as lm

MIGRATION_USER = {"email": "migracion@agpglass.com", "role": "ADMIN"}


def _load(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        sys.exit(f"{path}: se esperaba una lista JSON.")
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--formulas")
    ap.add_argument("--cotizaciones", action="append", default=[])
    ap.add_argument("--superseded-out", default="formulas_versiones_anteriores.json",
                    help="archivo donde se guardan las versiones anteriores de formulas repetidas")
    ap.add_argument("--apply", action="store_true", help="escribe en la base (sin esto: dry-run)")
    args = ap.parse_args()
    if not args.formulas and not args.cotizaciones:
        ap.error("indica --formulas y/o --cotizaciones")

    repo = None
    if args.apply:
        from app.services import pricing_repository as repo  # noqa: F811  (conecta solo con --apply)

    stats = {"ok": 0, "omitidas": 0, "invalidas": 0}  # + reemplazadas (formulas)

    def report(kind: str, key: str, status: str, extra: str = ""):
        print(f"[{kind}] {key}: {status} {extra}".rstrip())

    if args.formulas:
        vigentes, reemplazadas = lm.pick_latest_formulas(_load(args.formulas))
        if reemplazadas:
            Path(args.superseded_out).write_text(
                json.dumps(reemplazadas, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[formula] {len(reemplazadas)} versiones anteriores de codigos repetidos "
                  f"-> {args.superseded_out} (revisar con el area funcional)")
        stats["reemplazadas"] = len(reemplazadas)
        for legacy in vigentes:
            key = str(legacy.get("code"))
            try:
                payload = lm.map_formula(legacy)
            except ValidationError as exc:
                stats["invalidas"] += 1
                report("formula", key, "INVALIDA", str(exc.errors()[0]["msg"]))
                continue
            if repo:
                try:
                    repo.get_formula(payload["code"])
                    stats["omitidas"] += 1
                    report("formula", key, "ya existe, omitida")
                    continue
                except repo.NotFound:
                    repo.create_formula(payload, user=MIGRATION_USER, ip=None)
            stats["ok"] += 1
            report("formula", key, "migrada" if repo else "lista (dry-run)")

    seen: set[str] = set()
    for path in args.cotizaciones:
        for legacy in _load(path):
            key = str(legacy.get("id"))
            try:
                payload = lm.map_cotizacion(legacy)
            except ValidationError as exc:
                stats["invalidas"] += 1
                report("cotizacion", key, "INVALIDA", str(exc.errors()[0]["msg"]))
                continue
            if payload["codigo"] in seen:  # mismo id exportado desde dos navegadores
                stats["omitidas"] += 1
                report("cotizacion", key, "duplicada en los archivos, omitida")
                continue
            seen.add(payload["codigo"])
            if repo:
                try:
                    repo.get_cotizacion(payload["codigo"])
                    stats["omitidas"] += 1
                    report("cotizacion", key, "ya existe, omitida")
                    continue
                except repo.NotFound:
                    repo.create_cotizacion(payload, user=MIGRATION_USER, ip=None)
                    estado = lm.legacy_estado(legacy)
                    if estado != "abierta":
                        repo.set_estado_cotizacion(payload["codigo"], estado, user=MIGRATION_USER, ip=None)
            stats["ok"] += 1
            report("cotizacion", key, "migrada" if repo else "lista (dry-run)")

    print(f"\nResumen: {stats} | modo={'APPLY' if args.apply else 'DRY-RUN'}")
    return 1 if stats["invalidas"] else 0


if __name__ == "__main__":
    sys.exit(main())
