# CI/CD de la API — estado y configuración

Última actualización: 2026-10-05. Ver la sección "Hecho / Pendiente" al final.

## Decisión de arquitectura: una sola web app
Un desarrollo = un App Service (`REQUISITOS-DESPLIEGUE.md` del kit). Frontend y API son el mismo desarrollo, así que corren en
**`pricing-process-automation`** (plan `ASP-AGPColombia-8785`, **B1**): el frontend es el contenedor `main` (nginx, puerto 80) y la API es un
**contenedor sidecar** `api` (puerto 5000, el puerto fijo del kit). No se crea una segunda web app.

Consecuencias que hay que conocer:
- **No hay QA separado en Azure.** B1 no tiene slots. El gate previo a producción son las pruebas de CI + la aprobación humana del entorno `prod`.
  Si más adelante se quiere QA real: slot (requiere S1) o una app temporal.
- **La API no es pública por sí sola.** El sidecar solo es alcanzable desde el contenedor `main` en `localhost:5000`. Para usarla desde el navegador,
  el nginx del frontend debe hacer proxy de `/api`, `/auth` y `/health` hacia `127.0.0.1:5000` (cambio en el repo del frontend, que se despliega con ese
  repo). Mismo origen ⇒ sin CORS.
- Reiniciar o desplegar un contenedor puede reiniciar la app completa. Hay que desplegar fuera del horario de uso (avisar antes).
- Sidecars con B1: la documentación de Microsoft no declara un SKU mínimo, pero **no está verificado en este plan**. Se comprueba con el primer despliegue controlado.

## Flujo
| Evento | Qué pasa |
|---|---|
| Push a cualquier rama / PR | `ci.yml`: pruebas, auditoría de dependencias y build de la imagen (sin publicar) |
| Push a `main` (backend) | `cd.yml`: pruebas → imagen `pricing-process-automation-api:<SHA>` a ACR `agpcolit` → **espera aprobación (`prod`)** → actualiza solo el sidecar `api` |
| Manual | `cd.yml` con `image_tag` = rollback; `db-migrate.yml` aplica `backend/sql` (también bajo aprobación `prod`) |

Mientras `AZURE_CLIENT_ID` no exista como variable, `cd.yml` solo ejecuta las pruebas: no falla ni despliega.

## Nomenclatura (según el kit)
| Elemento | Valor | Fuente |
|---|---|---|
| App Service | `pricing-process-automation` (existente) | `docs/governance/naming-conventions.md` |
| Imagen API | `pricing-process-automation-api` | misma convención (`…-web` es la del frontend) |
| ACR | `agpcolit` | existente |
| Grupos Entra | `AGP-APP-PRICING-ADMIN`, `-ANALYST`, `-VIEWER` → app roles `Pricing.Admin/Analyst/Viewer` | `AGP-APP-PRICING-*` |
| Puerto / health / rama | `5000` / `/health` / `main` | `REQUISITOS-DESPLIEGUE.md` |
| Variables MSAL | `MSAL_TENANT_ID` (`10f1df46-3600-406b-8233-aa54d28fe447`), `MSAL_CLIENT_ID` | `CATALOGO-SECRETOS-POR-CAPACIDAD.md` |
| Secretos | Key Vault `agp-desarrollos-secrets`, nombre = variable con `_`→`-`; Managed Identity con `Key Vault Secrets User` solo sobre sus secretos | mismo catálogo |
| Base de datos | `agpc-productivity` en `agpcol.database.windows.net` (ya configurada en la API; 719 tablas `dbo`, sin colisiones con los nombres nuevos) | decisión del responsable |
| Tablas | `App_<Area>_<Desarrollo>_<Tabla>` en `dbo`, igual que 75 tablas existentes de `agpc-productivity` (p. ej. `App_SC_Cotizador_Tarifa_Aerea`); claves `Id<Entidad>` como `IdPregunta` | regla del responsable + patrón observado; el kit no define convención de tablas |

Tablas (`backend/sql/001_pricing_schema.sql`): `App_Finanzas_Pricing_Cotizacion`, `_CotizacionPieza`, `_Formula`, `_Auditoria`. Área asumida: **Finanzas** (PROYECTO_CONTEXT: "área VIP Finanzas / Pricing"). Rollback manual en `backend/sql/rollback/`.
Variables de BD con prefijo propio: hoy `SQL_*`; si TI lo exige, renombrar a `PRICING_DB_*` (el catálogo pide un prefijo que diga a qué base apunta).

## Hecho (a 2026-10-05)
- Plan `ASP-AGPColombia-8785`: F1 → **B1** (frontend verificado: Running; Easy Auth responde 401 a anónimos).
- GitHub (API): entorno **`prod`** (revisor BradlyAlejandroAGP, solo desde `main`), variables no secretas (`AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`,
  `AZURE_RESOURCE_GROUP`, `APP_NAME`, `ACR_PULL_IDENTITY_CLIENT_ID`, `SQL_SERVER`, `SQL_DATABASE`) y **`main` protegido** (PR + 1 aprobación + checks `test` y `docker-build`).
- Entra: app registrations de la API y la SPA, app roles, 3 grupos `AGP-APP-PRICING-*` y "Assignment required" (ver `docs/security/msal-setup.md`).
- Tablas `App_Finanzas_Pricing_*` creadas en `agpc-productivity`; CRUD probado de punta a punta contra la base real (con limpieza).
- Código: MSAL JWT, Managed Identity para SQL (`SQL_AUTH_MODE=msi`), diagnóstico de BD solo ADMIN, CORS con `If-Match`/`ETag`, puerto 5000.
- Frontend (PR AGP-Corp/pricing-process-automation#1): capa de sincronización apagada por defecto + proxy `/api` de nginx.
- Auto-fix del PR #1 activado.

## Pendiente (todo requiere a una persona con permisos; ver `runbook-primer-despliegue.md`)
1. **`AZURE_CLIENT_ID`**: ejecutar `infra/setup-oidc.sh` (Owner del RG). Sin esto el CD solo ejecuta pruebas.
2. **Grants SQL** de mínimo privilegio: `backend/sql/manual/002_grants_pricing_identity.sql` (admin Entra de SQL).
3. **Usuarios de prueba** en `AGP-APP-PRICING-ANALYST` y uno fuera de los grupos, para verificar el token MSAL real.
4. **Excluir `/api/*` de Easy Auth** (runbook, paso 3) y aplicar las app settings (paso 2): reinician la app, en ventana acordada.
5. ~~Aprobación de los PRs~~: ambos PRs (API #1 y frontend #1) ya están fusionados en `main` (2026-10-05; sin aprobación registrada en GitHub: se integraron con permiso de administrador).
   **Despliegue automático** (ADR-001) ACTIVO para `BradlyAlejandroAGP` y `Maria-GalindoC`; los cambios asistidos por IA siguen pasando por aprobación en `prod`. Registrar la aprobación formal de Gobierno/Tech Lead/DevOps Owner.
6. **Seguridad de la base (TI):** los servidores `agpcol` y `agpcolsap` tienen una regla de firewall `INTERNET` (0.0.0.0–255.255.255.255). No se modificó.
7. **Credenciales propias de pricing** en Key Vault si se usara el modo `sql` (no reutilizar `AGPCOL-USER/PASSWORD`). Con `msi` no hacen falta.
8. Verificaciones que solo se pueden hacer en Azure: sidecar en B1 y `Authorization: Bearer` a través de Easy Auth.
