$ErrorActionPreference = 'Stop'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdministrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdministrator) {
    Write-Host 'Windows solicitará autorización para ejecutar el sistema heredado.' -ForegroundColor Yellow
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', ('"' + $PSCommandPath + '"')
    )
    exit 0
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$legacyRoot = Join-Path $projectRoot 'legado-local'
$firebirdRoot = Join-Path $legacyRoot 'firebird-2.5-tools-x86'
$executable = Join-Path $legacyRoot 'Distribuidora.exe'

if (-not (Test-Path -LiteralPath $executable) -or -not (Test-Path -LiteralPath (Join-Path $firebirdRoot 'bin\fbserver.exe'))) {
    Write-Host 'Faltan los componentes locales del sistema original.' -ForegroundColor Red
    Write-Host 'Consulta docs\LEGADO.md para volver a prepararlos.'
    Read-Host 'Presiona Enter para salir'
    exit 1
}

$systemIni = Join-Path $env:WINDIR 'newruta.ini'
Copy-Item -LiteralPath (Join-Path $legacyRoot 'newruta.ini') -Destination $systemIni -Force

$existingServer = Get-Process -Name 'fbserver' -ErrorAction SilentlyContinue | Select-Object -First 1
$startedHere = $false
if (-not $existingServer) {
    $existingServer = Start-Process -FilePath (Join-Path $firebirdRoot 'bin\fbserver.exe') -ArgumentList '-a' -WorkingDirectory $firebirdRoot -WindowStyle Hidden -PassThru
    $startedHere = $true
    Start-Sleep -Seconds 2
}

try {
    $legacyApp = Start-Process -FilePath $executable -WorkingDirectory $legacyRoot -PassThru
    Write-Host 'Sistema original iniciado. Si aparece el aviso de fecha-hora, pulsa OK.' -ForegroundColor Green
    Wait-Process -Id $legacyApp.Id
}
finally {
    if ($startedHere -and $existingServer -and -not $existingServer.HasExited) { Stop-Process -Id $existingServer.Id }
    Remove-Item -LiteralPath $systemIni -Force -ErrorAction SilentlyContinue
}
