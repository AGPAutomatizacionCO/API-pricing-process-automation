# Spec: persistencia y CRUD de Pricing (Fase 2 backend)

Estado: BORRADOR, pendiente de revisión humana (funcional: mgalindo; TI) antes de aplicar en cualquier base real.

## Problema
El frontend guarda cotizaciones en `localStorage` (`agp_cotizaciones_v1`) y la biblioteca de fórmulas en `formula_library.json` + `localStorage`. No hay datos compartidos, ni auditoría, ni control de acceso real. La API actual solo tiene endpoints de diagnóstico (`/api/db/*`) y no existen tablas de negocio.

## Alcance de esta entrega
- `backend/sql/001_pricing_schema.sql`: tablas `App_Finanzas_Pricing_Cotizacion`, `_cotizacion_pieza`, `_formula`, `_auditoria`.
- CRUD en `/api/pricing/cotizaciones` y `/api/pricing/formulas`.
- Concurrencia optimista con `ROWVERSION` (ETag / `If-Match`), borrado lógico y auditoría en tabla.

## Roles
| Operación | VIEWER | ANALYST | ADMIN |
|---|---|---|---|
| Leer cotizaciones y fórmulas | sí | sí | sí |
| Crear / editar / archivar cotización | no | sí | sí |
| Eliminar cotización (lógico) | no | no | sí |
| Crear / editar / eliminar fórmula | no | no | sí |

## Fuera de alcance (siguientes tareas)
- Carga versionada de Budget, Insumos, Producción, Homologación y BD Pricing (tablas de referencia).
- Migración de datos existentes de `localStorage` / `formula_library.json`.
- Cambio de Easy Auth a MSAL (validación de JWT `Authorization: Bearer`).
- Cambios en el frontend para consumir la API; retiro de Excel de la imagen.
- Managed Identity / Key Vault para la conexión SQL; Row-Level Security.
- CI/CD automático (OIDC + staging).

## Riesgos
- `SnapshotJson` y `DetalleJson` guardan estructuras del HTML actual; si el frontend cambia su forma, hay que versionar el snapshot.
- Hoy los roles salen de variables de entorno; hasta MSAL/grupos Entra siguen siendo listas de correos.
- El esquema no se ha aplicado a ninguna base. Revisar con TI antes de ejecutarlo.

## Criterios de aceptación
- Un VIEWER no puede escribir; un ANALYST no puede borrar; solo ADMIN gestiona fórmulas.
- Editar con ETag desactualizado devuelve 409; sin `If-Match` devuelve 428.
- Cada escritura deja una fila en `dbo.App_Finanzas_Pricing_Auditoria`.
- `pytest backend/tests` en verde.
