# Bootstrap humano de la identidad OIDC para el CD de la API (mismo estilo que la Mesa: visible, idempotente, sin tokens).
# Ejecutar UNA vez en PowerShell, con una cuenta Owner del grupo de recursos. No lo ejecuta ningun workflow ni agente.
$ErrorActionPreference = 'Stop'
$repo = 'AGPAutomatizacionCO/API-pricing-process-automation'
$rg = 'AGP-Colombia'; $app = 'pricing-process-automation'; $acr = 'agpcolit'
$name = 'oidc-msi-pricing-process-automation-api'

$cuenta = az account show --query user.name -o tsv 2>$null
if ($LASTEXITCODE -ne 0) { az login --use-device-code; $cuenta = az account show --query user.name -o tsv }
Write-Host "Cuenta: $cuenta | Suscripcion: $(az account show --query id -o tsv)"
if ((Read-Host "Crear la identidad '$name' y asignar roles minimos en '$rg'? (escribe si)") -ne 'si') { throw 'cancelado' }

$id = az identity show -g $rg -n $name -o json 2>$null | ConvertFrom-Json
if (-not $id) { $id = az identity create -g $rg -n $name -o json | ConvertFrom-Json }

# Una credencial por tipo de job de cd.yml: build (rama main) y deploy (entorno prod, o prod-auto para cambios de personas autorizadas: ADR-001).
foreach ($c in @(@{n='gh-main'; s="repo:${repo}:ref:refs/heads/main"}, @{n='gh-prod'; s="repo:${repo}:environment:prod"}, @{n='gh-prod-auto'; s="repo:${repo}:environment:prod-auto"})) {
  $ex = az identity federated-credential list -g $rg --identity-name $name --query "[?name=='$($c.n)']" -o json | ConvertFrom-Json
  if (-not $ex) {
    az identity federated-credential create -g $rg --identity-name $name --name $c.n --issuer 'https://token.actions.githubusercontent.com' --subject $c.s --audiences 'api://AzureADTokenExchange' -o none
  } elseif ($ex[0].subject -ne $c.s) { throw "La credencial $($c.n) existe con otro subject: $($ex[0].subject)" }
}

# Minimo privilegio: subir imagenes al ACR y actualizar SOLO esta web app.
$scopes = @(
  @{ role = 'AcrPush';             scope = (az acr show -n $acr --query id -o tsv) },
  @{ role = 'Website Contributor'; scope = (az webapp show -g $rg -n $app --query id -o tsv) }
)
foreach ($r in $scopes) {
  $has = az role assignment list --assignee $id.principalId --scope $r.scope --role $r.role -o json | ConvertFrom-Json
  if (-not $has) { az role assignment create --assignee-object-id $id.principalId --assignee-principal-type ServicePrincipal --role $r.role --scope $r.scope -o none }
}
Write-Host 'Bootstrap completado.'
Write-Host "AZURE_CLIENT_ID=$($id.clientId)"
Write-Host "Cargar:  gh variable set AZURE_CLIENT_ID --repo $repo --body $($id.clientId)"
