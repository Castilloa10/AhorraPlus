@echo off
setlocal
cd /d "%~dp0"
title Ahorra+ - Inicio
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" iniciar.py
) else (
    python iniciar.py
)
if errorlevel 1 pause
