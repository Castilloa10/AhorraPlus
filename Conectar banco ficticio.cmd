@echo off
setlocal
title Ahorra+ - Banco ficticio SANDBOX
cd /d "%~dp0"
if exist "%~dp0..\..\work\ahorra-python" set "PYTHONPATH=%~dp0..\..\work\ahorra-python;%PYTHONPATH%"
echo Se reiniciara solo el servidor de pruebas de Ahorra+ si ya esta abierto y se identifica.
echo Abre http://127.0.0.1:8767/ en este mismo navegador para autorizar Mock ASPSP.
echo Solo banco ficticio. No conecta Openbank. Pulsa Ctrl+C para detener el servidor.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" iniciar_banco_ficticio.py
) else (
  python iniciar_banco_ficticio.py
)
pause
