#!/usr/bin/env bash
# Crea la identidad que usa GitHub Actions (OIDC, sin secretos) para desplegar la API.
# Ejecutar UNA vez, con una cuenta que sea Owner (o User Access Administrator) del grupo de recursos.
# No se ejecuta desde ningun workflow. Es idempotente en lo posible: si algo ya existe, avisa y sigue.
#
# Patron de la zona: una identidad administrada por repo (como las "oidc-msi-xxxx" del Deployment Center).
# Se usan DOS credenciales federadas porque cd.yml tiene dos tipos de job:
#   - build   (sin Environment)  -> subject  ref:refs/heads/main
#   - deploy  (Environment prod) -> subject  environment:prod   (el que exige aprobacion humana)
set -euo pipefail

REPO="AGPAutomatizacionCO/API-pricing-process-automation"
RG="AGP-Colombia"
APP="pricing-process-automation"
ACR="agpcolit"
IDENTITY="oidc-msi-pricing-process-automation-api"

SUB=$(az account show --query id -o tsv)
echo "Suscripcion: $SUB | cuenta: $(az account show --query user.name -o tsv)"
read -r -p "Crear identidad '$IDENTITY' y asignar roles en '$RG'? (escribe si) " ok
[ "$ok" = "si" ] || { echo "cancelado"; exit 1; }

az identity create -g "$RG" -n "$IDENTITY" -o none
CLIENT_ID=$(az identity show -g "$RG" -n "$IDENTITY" --query clientId -o tsv)
PRINCIPAL_ID=$(az identity show -g "$RG" -n "$IDENTITY" --query principalId -o tsv)

for pair in "gh-main:ref:refs/heads/main" "gh-prod:environment:prod"; do
  name="${pair%%:*}"; subject="repo:${REPO}:${pair#*:}"
  az identity federated-credential create -g "$RG" --identity-name "$IDENTITY" --name "$name" \
    --issuer "https://token.actions.githubusercontent.com" --subject "$subject" \
    --audiences "api://AzureADTokenExchange" -o none || echo "aviso: credencial $name ya existia"
done

# Minimo privilegio: subir imagenes al ACR y actualizar SOLO esta web app.
ACR_ID=$(az acr show -n "$ACR" --query id -o tsv)
APP_ID=$(az webapp show -g "$RG" -n "$APP" --query id -o tsv)
az role assignment create --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal \
  --role AcrPush --scope "$ACR_ID" -o none || echo "aviso: AcrPush ya asignado"
az role assignment create --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal \
  --role "Website Contributor" --scope "$APP_ID" -o none || echo "aviso: Website Contributor ya asignado"

echo
echo "AZURE_CLIENT_ID = $CLIENT_ID"
echo "Para activar el CD:  gh variable set AZURE_CLIENT_ID --repo $REPO --body $CLIENT_ID"
