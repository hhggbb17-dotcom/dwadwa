$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceRoot = Split-Path -Parent $projectRoot
$database = Join-Path $sourceRoot 'CARLOSE.FDB'
$firebirdRoot = Join-Path $projectRoot 'legado-local\firebird-2.5-tools-x86'
$output = Join-Path $projectRoot 'PublicacionesEspindola\data\store.json'

if (-not (Test-Path -LiteralPath $database)) { throw "No se encontró $database" }
if (-not (Test-Path -LiteralPath (Join-Path $firebirdRoot 'bin\fbserver.exe'))) { throw 'Primero prepara los componentes Firebird del legado.' }

$answer = Read-Host 'Esto reemplazará los catálogos actuales (se conservará una copia). Escribe IMPORTAR para continuar'
if ($answer -cne 'IMPORTAR') { Write-Host 'Importación cancelada.'; exit 0 }

$server = Start-Process -FilePath (Join-Path $firebirdRoot 'bin\fbserver.exe') -ArgumentList '-a' -WorkingDirectory $firebirdRoot -WindowStyle Hidden -PassThru
try {
    Start-Sleep -Seconds 2
    dotnet run --project (Join-Path $projectRoot 'tools\Migrador\Migrador.csproj') --configuration Release -- $database $output
    if ($LASTEXITCODE -ne 0) { throw "El migrador terminó con código $LASTEXITCODE" }
}
finally {
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id }
}
