# Migración de datos de Pricing a la base (guía para la dueña funcional)

Destino: tablas `dbo.App_Finanzas_Pricing_*` en `agpc-productivity`. Las tablas ya existen y el CRUD fue probado de punta a punta
(21 comprobaciones, con limpieza). **Hoy no hay datos de pricing cargados.**

> Importante: mientras el HTML no consuma la API, lo que se cargue aquí **no se ve en la aplicación**; el HTML sigue leyendo su
> `localStorage`. La carga deja los datos listos y respaldados en la base para cuando el frontend se conecte.

## Requisitos
- Python 3.12 y las dependencias: `pip install -r requirements.txt`.
- Acceso de escritura a la base: un archivo `backend/.env` con `SQL_SERVER`, `SQL_DATABASE`, `SQL_USERNAME`, `SQL_PASSWORD`
  que entrega **TI** (no se comparte por chat ni se sube al repo; `.env` está en `.gitignore`).
- Driver `ODBC Driver 18 for SQL Server` instalado.

## 1. Fórmulas (`formula_library.json`)
Siempre empezar en simulación (no se conecta a la base):

```bash
cd backend
python -m scripts.migrate_legacy --formulas ../../pricing-process-automation/formula_library.json
```

Resultado esperado hoy: 44 registros → **29 vigentes + 15 versiones anteriores** (13 códigos repetidos).
Las versiones anteriores quedan en `formulas_versiones_anteriores.json` para revisarlas.

**Decisión funcional (la toma María):** el script deja como vigente la versión con `savedAt` más reciente de cada código, sin distinguir
mayúsculas (`L15-5` = `l15-5`). Si la vigente debe ser otra, borrar del JSON de entrada las versiones que NO se quieren
(o editar `savedAt`) y repetir la simulación hasta que el resultado sea el correcto.

Cuando esté conforme:

```bash
python -m scripts.migrate_legacy --formulas ../../pricing-process-automation/formula_library.json --apply
```

## 2. Cotizaciones (`localStorage` de cada navegador)
Cada usuario exporta lo suyo desde la consola del navegador de la app (F12 → Console) y guarda el resultado en un `.json`:

```js
copy(localStorage.getItem('agp_cotizaciones_v1'))
```

Luego (simulación primero, después `--apply`); se pueden pasar varios archivos y los ids repetidos se omiten:

```bash
python -m scripts.migrate_legacy --cotizaciones usuario1.json --cotizaciones usuario2.json
python -m scripts.migrate_legacy --cotizaciones usuario1.json --cotizaciones usuario2.json --apply
```

## Garantías del script
- **Idempotente:** lo que ya existe se omite; se puede repetir sin duplicar.
- **No destruye nada:** solo inserta. Lo inválido se reporta y se salta (el código de salida es 1 si hubo inválidos).
- Cada carga queda en `App_Finanzas_Pricing_Auditoria` a nombre de `migracion@agpglass.com`.
- Las cotizaciones conservan su `estado` (abierta/archivada) y el registro original completo dentro del snapshot (`_legacy`).

## Verificación posterior (SQL)
```sql
SELECT (SELECT COUNT(*) FROM dbo.App_Finanzas_Pricing_Formula     WHERE Eliminada = 0) AS formulas,
       (SELECT COUNT(*) FROM dbo.App_Finanzas_Pricing_Cotizacion  WHERE Eliminada = 0) AS cotizaciones;
```

## Si hay que deshacer
Borrado lógico por la API (rol ADMIN) o, con autorización de TI, `backend/sql/rollback/001_drop_pricing.sql` (**borra tablas y datos**).
