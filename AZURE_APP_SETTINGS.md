# Variables de entorno para Azure App Service
# Configurar en: App Service → Settings → Environment variables

## Cómo configurarlas
1. Ir a portal.azure.com
2. Abrir `pricing-process-automation`
3. Settings → Environment variables
4. Agregar cada variable con su valor real

## Variables requeridas

| Variable | Valor de ejemplo | Descripción |
|---|---|---|
| `APP_NAME` | `AGP Pricing Process API` | Nombre de la app |
| `APP_ENV` | `production` | Entorno (cambiar de local a production) |
| `APP_HOST` | `0.0.0.0` | Host |
| `APP_PORT` | `8000` | Puerto |
| `SQL_SERVER` | `tu-server.database.windows.net` | Servidor Azure SQL |
| `SQL_DATABASE` | `nombre-bd` | Base de datos |
| `SQL_DRIVER` | `ODBC Driver 17 for SQL Server` | Driver ODBC |
| `SQL_TRUSTED_CONNECTION` | `false` | En Azure usar false |
| `SQL_USERNAME` | `tu-usuario` | Usuario SQL |
| `SQL_PASSWORD` | `tu-password` | Password SQL (usar Key Vault) |
| `FRONTEND_ORIGINS` | `https://pricing-process-automation-xxx.azurewebsites.net` | URL del App Service |
| `ACCESS_POLICY_ENABLED` | `true` | Activar control de acceso |
| `ADMIN_USERS` | `mgalindo@agpglass.com,bmartin@agpglass.com` | Admins separados por coma |
| `ANALYST_USERS` | | Analistas |
| `VIEWER_USERS` | | Solo lectura |
| `ENTRA_TENANT_ID` | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | Tenant ID de Azure AD |
| `ENTRA_CLIENT_ID` | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | Client ID de la app registrada |
| `ENTRA_ISSUER` | `https://login.microsoftonline.com/<TENANT_ID>/v2.0` | Issuer Entra ID |
| `ENTRA_AUDIENCE` | `<CLIENT_ID>` | Audience (igual al Client ID) |
| `SESSION_COOKIE_NAME` | `pricing_session` | Nombre de la cookie |
| `SESSION_SECRET_KEY` | `clave-larga-y-segura-minimo-32-chars` | ⚠️ Generar una clave segura |
| `SESSION_EXPIRE_MINUTES` | `480` | 8 horas de sesión |
| `SESSION_COOKIE_SECURE` | `true` | En producción siempre true |
| `SESSION_COOKIE_SAMESITE` | `lax` | SameSite policy |

## ⚠️ Secrets en GitHub Actions (configurar en repo → Settings → Secrets)

| Secret | Descripción |
|---|---|
| `AZURE_WEBAPP_PUBLISH_PROFILE` | Descargar desde Azure: App Service → Download publish profile |
| `GH_PAT_MARIA_REPO` | Token PAT de GitHub con acceso al repo de Maria (AGP-Corp/pricing-process-automation) |
