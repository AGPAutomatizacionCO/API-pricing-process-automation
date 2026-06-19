# Operations Runbook

## Verify App Service

```powershell
az webapp show --name <APP_NAME> --resource-group <RESOURCE_GROUP>
```

---

## Restart App Service

```powershell
az webapp restart --name <APP_NAME> --resource-group <RESOURCE_GROUP>
```

---

## Start App Service

```powershell
az webapp start --name <APP_NAME> --resource-group <RESOURCE_GROUP>
```

---

## Stop App Service

```powershell
az webapp stop --name <APP_NAME> --resource-group <RESOURCE_GROUP>
```

---

## List ACR Repositories

```powershell
az acr repository list --name agpcolit -o table
```

---

## List Image Tags

```powershell
az acr repository show-tags --name agpcolit --repository api-pricing-process-automation -o table
```

---

## Check Application Logs

```powershell
az webapp log tail --name <APP_NAME> --resource-group <RESOURCE_GROUP>
```
