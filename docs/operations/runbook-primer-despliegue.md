# Runbook: primer despliegue de la API de Pricing (sidecar) y activación de MSAL

Estado: BORRADOR para ejecución humana en ventana acordada. **Nada de esto se ha ejecutado en Azure.**
Quién: alguien con Owner del RG `AGP-Colombia` + admin Entra de SQL. Duración estimada: 1 h. Avisar a los usuarios antes (la web app puede reiniciarse).

## 0. Pre-requisitos (sin impacto en usuarios)
| # | Qué | Dueño | Cómo saber que está |
|---|---|---|---|
| 0.1 | PR #1 de la API aprobado y mergeado, CI en verde | revisor humano | rama `main` con `cd.yml` |
| 0.2 | `AZURE_CLIENT_ID` cargado | Owner del RG | `infra/setup-oidc.sh` ejecutado; `gh variable list` lo muestra |
| 0.3 | Grants SQL (mínimo privilegio) | admin Entra de SQL | `backend/sql/manual/002_grants_pricing_identity.sql` ejecutado y verificado |
| 0.4 | Usuarios de prueba en los grupos `AGP-APP-PRICING-*` | TI | uno en `-ANALYST`, otro fuera de todos |
| 0.5 | PR del frontend (proxy `/api` + capa de sync apagada) mergeado y **desplegado primero** | dueña funcional + TI | `deploy.yml` manual del frontend |

## 1. Desplegar el frontend con el proxy (la capa de sync sigue apagada)
`deploy.yml` del repo del frontend (manual, escribir "deploy"). Verificar que la app carga y que `/api/` responde **502** (sin sidecar todavía).
Ojo: producción corre hoy `pricing-frontend:1138307` (6 jul); este despliegue también publica los cambios de septiembre y octubre de María.

## 2. App settings de la web app (reinicia la app)
```bash
az webapp config appsettings set -g AGP-Colombia -n pricing-process-automation --settings \
  APP_ENV=production MSAL_AUTH_ENABLED=true MSAL_TENANT_ID=10f1df46-3600-406b-8233-aa54d28fe447 \
  MSAL_CLIENT_ID=f3db0138-b23c-4689-80b1-93093db50550 MSAL_REQUIRED_SCOPE=access_as_user \
  EASY_AUTH_ENABLED=true SQL_SERVER=agpcol.database.windows.net SQL_DATABASE=agpc-productivity \
  SQL_AUTH_MODE=msi SQL_MSI_CLIENT_ID=f213fbe2-1a27-4fc0-bdfc-0b49bd821218 \
  FRONTEND_ORIGINS=https://pricing-process-automation-hcbugtgqd4c4guak.brazilsouth-01.azurewebsites.net
```
- Todos los contenedores comparten estas variables. **Nunca** poner contraseñas aquí en texto plano: si se usara el modo `sql`, referenciar Key Vault
  (`@Microsoft.KeyVault(VaultName=…;SecretName=…)`) con un secreto **propio de pricing** (no reutilizar `AGPCOL-USER/PASSWORD`, que usan otras apps).
- Anotar los valores anteriores antes de cambiar (rollback).

## 3. Excluir `/api` de Easy Auth (decisión de seguridad: revisar con TI)
Hoy Easy Auth exige login en todo (`RedirectToLoginPage`, sin rutas excluidas). Un `Authorization: Bearer` de MSAL puede chocar con Easy Auth. La API valida el JWT
por sí misma (firma, `aud`, `iss`, `tid`, `exp`, scope y rol), así que se excluye `/api/*` y `/auth/me`:
```bash
az rest --method get --url "https://management.azure.com/subscriptions/bd16e31f-bdf1-4006-8d32-617df0c1e092/resourceGroups/AGP-Colombia/providers/Microsoft.Web/sites/pricing-process-automation/config/authsettingsV2?api-version=2023-12-01" > authsettingsV2.backup.json
# editar globalValidation.excludedPaths = ["/api/*", "/auth/me"] y aplicar con az rest --method put … (ver backup para rollback)
```
Efecto: `/api/*` queda accesible sin cookie de Easy Auth, **protegido solo por el JWT**. Verificar con una petición sin token: debe dar **401** de la API, nunca 200.

## 4. Primer despliegue del sidecar
Desde GitHub → Actions → **CD** (rama `main`) → aprobar el entorno `prod`. El job registra la imagen anterior y crea el sidecar `api` (puerto 5000).
Si es la primera vez: comprobar que **B1 acepta el sidecar** (la documentación de Microsoft no declara restricción de plan, pero no está verificado aquí).

## 5. Verificación
1. Web app `Running` y el frontend carga igual que antes.
2. `GET https://<host>/api-health` → 200 (requiere sesión de Easy Auth, o exclusión si TI decide publicarlo).
3. Con el usuario de prueba del grupo ANALYST: login MSAL → token con `scp=access_as_user` y `roles=["Pricing.Analyst"]`; `GET /auth/me` → rol `ANALYST`.
4. Con el usuario fuera de grupos: no obtiene token (Assignment required) → 401/403.
5. Crear una cotización de prueba desde la UI con la sincronización encendida, confirmar la fila en `App_Finanzas_Pricing_Cotizacion`, y borrarla.

## 6. Activar la sincronización en el frontend
`app-config.js`: `enabled: true`, `auth: 'msal'` (o `'easyauth'` si el Bearer no pasa) → PR → despliegue manual. Con `false` se vuelve al comportamiento anterior.

## Rollback (de lo más reciente a lo más antiguo)
1. Frontend: `app-config.js` `enabled:false` (o redeploy del tag anterior con `deploy.yml`).
2. Sidecar: `az webapp sitecontainers delete -g AGP-Colombia -n pricing-process-automation --container-name api` (o CD con `image_tag` anterior).
3. Easy Auth: aplicar `authsettingsV2.backup.json`.
4. App settings: restaurar los valores anotados en el paso 2.
5. SQL: `REVOKE` del bloque de reversión de `002_grants_pricing_identity.sql`. Las tablas no se borran (`backend/sql/rollback/` solo con autorización).
