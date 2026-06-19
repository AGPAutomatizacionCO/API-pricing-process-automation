# API corporativa para Pricing Process Automation.

La API expone consultas controladas a bases de datos empresariales,
utiliza Microsoft Entra ID para autenticación,
Azure SQL como origen de datos
y Azure Key Vault para la gestión futura de secretos.

Estado: MVP técnico validado

✓ FastAPI
✓ Docker
✓ Azure SQL
✓ Easy Auth
✓ Control de roles
✓ Auditoría
✓ Azure Container Registry

Pendiente:
- Despliegue simultáneo Front + API en Azure
- Key Vault
- Catálogo corporativo de roles

Structure:

Frontend
    ↓
Azure App Service
    ↓
Microsoft Entra ID
    ↓
FastAPI
    ↓
Azure SQL