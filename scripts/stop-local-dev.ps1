$ErrorActionPreference = "SilentlyContinue"

Write-Host "Stopping local Pricing Process Automation services..." -ForegroundColor Cyan

$Ports = @(8000, 5173)

foreach ($Port in $Ports) {
    $Connections = netstat -ano | Select-String ":$Port"

    foreach ($Connection in $Connections) {
        $Parts = ($Connection.ToString() -split "\s+") | Where-Object { $_ -ne "" }
        $PidValue = $Parts[-1]

        if ($PidValue -match "^\d+$") {
            Write-Host "Stopping process on port $Port. PID: $PidValue"
            taskkill /PID $PidValue /F | Out-Null
        }
    }
}

Write-Host "Local services stopped." -ForegroundColor Green