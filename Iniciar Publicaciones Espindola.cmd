@echo off
title Publicaciones Espindola
cd /d "%~dp0PublicacionesEspindola"
start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5188'"
dotnet run --configuration Release
pause
