@echo off
title Publicaciones Espindola
cd /d "%~dp0PublicacionesEspindola"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" app.py
) else (
  python app.py
)
pause
