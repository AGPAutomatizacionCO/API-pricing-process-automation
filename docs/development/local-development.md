# Local Development

## Build Docker Image

```powershell
docker build -t api-pricing-process-automation:local .
```

---

## Run Container

```powershell
docker run --rm -p 8000:8000 `
-e APP_ENV=local `
-e LOCAL_AUTH_ENABLED=true `
-e LOCAL_AUTH_EMAIL=user@agpglass.com `
-e ADMIN_USERS=user@agpglass.com `
api-pricing-process-automation:local
```

---

## Health Validation

```powershell
Invoke-RestMethod http://127.0.0.1:8000/auth/me
```

---

## Database Validation

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/db/test
```

---

## Requirements

* Docker Desktop
* Python 3.12+
* Azure CLI
* SQL credentials
