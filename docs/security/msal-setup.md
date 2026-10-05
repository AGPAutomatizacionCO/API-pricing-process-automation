# Migración Easy Auth → MSAL

Estado: BORRADOR, requiere revisión de TI (los pasos 1–3 se hacen en el portal de Entra con permisos de TI).

## Modelo
- El navegador inicia sesión con MSAL (Authorization Code + PKCE) y pide un access token para la API.
- La API valida firma (JWKS del tenant), `aud`, `iss`, `tid`, `exp` y el scope `access_as_user`.
- El rol sale del claim `roles` (app roles asignados a grupos en Entra). Ya no se usan listas de correos.
- Tokens sin usuario (client credentials) se rechazan.

## 1. App registration de la API
- Exponer API: Application ID URI `api://<MSAL_CLIENT_ID>`, scope delegado `access_as_user`.
- `accessTokenAcceptedVersion = 2` en el manifiesto (la API acepta v1 y v2 de todos modos).
- App roles (tipo Users/Groups): `Pricing.Admin`, `Pricing.Analyst`, `Pricing.Viewer`.

## 2. App registration del frontend (SPA)
- Plataforma Single-page application, redirect URIs: URL de producción, staging y `http://localhost:5173`.
- Permiso delegado a la API: `access_as_user` (con consentimiento de administrador).

## 3. Roles por grupo
- Enterprise applications → app de la API → Users and groups: asignar grupos de Entra a cada app role.
- Activar "Assignment required" para que solo usuarios asignados obtengan token.

## 4. Variables de la API (App Service)
`MSAL_AUTH_ENABLED=true`, `MSAL_TENANT_ID`, `MSAL_CLIENT_ID`; al terminar la transición `EASY_AUTH_ENABLED=false`
y desactivar Easy Auth en el App Service (así la API recibe el Bearer directamente).

## 5. Frontend (referencia)
```js
import { PublicClientApplication } from "@azure/msal-browser";
const msal = new PublicClientApplication({
  auth: { clientId: SPA_CLIENT_ID, authority: `https://login.microsoftonline.com/${TENANT_ID}`,
          redirectUri: window.location.origin },
  cache: { cacheLocation: "sessionStorage" },
});
await msal.initialize();
const scopes = [`api://${API_CLIENT_ID}/access_as_user`];
// loginRedirect({ scopes }) la primera vez; luego:
const { accessToken } = await msal.acquireTokenSilent({ scopes, account: msal.getAllAccounts()[0] });
fetch("/api/pricing/cotizaciones", { headers: { Authorization: `Bearer ${accessToken}` } });
```

## Transición sin corte
Con `MSAL_AUTH_ENABLED=true` y `EASY_AUTH_ENABLED=true` la API acepta ambos métodos (Bearer primero). Un Bearer inválido
devuelve 401 sin caer a Easy Auth. Cuando el frontend ya use MSAL, apagar Easy Auth.

## Pruebas
`pytest backend/tests/test_msal_auth.py`: token válido, expirado, audiencia/tenant/issuer erróneos, sin scope,
sin rol, firmado con otra llave, basura, y header X-MS-* falsificado con Easy Auth apagado.

## Registros creados (2026-10-05, por agente de configuración, revisados por humano)
Identificadores (no son secretos). Tenant `10f1df46-3600-406b-8233-aa54d28fe447`.

| Recurso | Nombre | ID |
|---|---|---|
| App registration API | `agp-co-finanzas-pricing-api` | appId `f3db0138-b23c-4689-80b1-93093db50550` (= `MSAL_CLIENT_ID`) |
| App registration SPA | `agp-co-finanzas-pricing-spa` | appId `df75dc70-5982-4a44-93be-c1f41a71cb5a` (= `clientId` de msal-browser) |
| Grupos | `AGP-APP-PRICING-ADMIN` / `-ANALYST` / `-VIEWER` | `14f8f4c4-…` / `7dca9e80-…` / `159b6fc4-…` (sin miembros) |

- API: single-tenant, token v2, scope `access_as_user`, app roles `Pricing.Admin/Analyst/Viewer`, "Assignment required" activado.
- SPA: plataforma SPA (sin secret), redirects a producción y `http://localhost:5173`, SPA preautorizada en el scope de la API.
- Pendiente: usuarios de prueba (uno en `AGP-APP-PRICING-ANALYST`, otro fuera de todos los grupos) para verificar el token real.
- `AGPCOL-Secrets` es la app registration del Easy Auth actual: no se toca. `pricing-deploy` NO sirve para el CD (sin credenciales federadas, Contributor amplio).
- App settings de la web app (aplicar en ventana acordada; reinician la app): `MSAL_AUTH_ENABLED=true`, `MSAL_TENANT_ID`, `MSAL_CLIENT_ID`,
  `MSAL_REQUIRED_SCOPE=access_as_user`, y `EASY_AUTH_ENABLED=true` solo durante la transición.
