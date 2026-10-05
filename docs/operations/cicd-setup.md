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

## Hecho (2026-10-05)
- Plan `ASP-AGPColombia-8785`: F1 → **B1** (frontend verificado: Running, Easy Auth responde 401 a anónimos).
- GitHub `AGPAutomatizacionCO/API-pricing-process-automation`: entorno **`prod`** (revisor: BradlyAlejandroAGP; despliegue solo desde `main`) y variables
  `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `APP_NAME`, `ACR_PULL_IDENTITY_CLIENT_ID` (ninguna es secreta).
- Código alineado con el kit: puerto 5000, `MSAL_*`, imagen y entorno nombrados según la convención.

## Pendiente
1. **Identidad OIDC de GitHub:** ejecutar `infra/setup-oidc.sh` una vez, con una cuenta Owner del grupo de recursos. Crea la identidad administrada `oidc-msi-pricing-process-automation-api` con DOS credenciales federadas (`ref:refs/heads/main` para el job build y `environment:prod` para el deploy con aprobación), le da `AcrPush` sobre `agpcolit` y `Website Contributor` solo sobre la web app, y muestra el `AZURE_CLIENT_ID` para cargarlo como variable del repo. Hasta que esa variable exista, el CD solo ejecuta pruebas.
2. **Ejecutar `001_pricing_schema.sql` en `agpc-productivity`** (SSMS/Azure Data Studio con un login con DDL, o `db-migrate.yml` cuando exista la identidad OIDC) y crear el usuario contenido para la Managed Identity (`db_datareader`/`db_datawriter`) y usuario DDL solo para `db-migrate.yml`.
3. **App registrations MSAL** (API y SPA), app roles y grupos `AGP-APP-PRICING-*` (`docs/security/msal-setup.md`).
4. **Proxy `/api` en el nginx del frontend** y la variable `API_HEALTH_URL` para el smoke test público.
5. **Key Vault**: secretos de conexión SQL bajo `agp-desarrollos-secrets` y acceso de la Managed Identity.
6. Proteger `main` (PR obligatorio + CI verde) y añadir un segundo revisor en `prod`.
7. Primer despliegue del sidecar **en ventana acordada**, avisando a los usuarios.
