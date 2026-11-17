@echo off
setlocal
title Ahorra+ - Retorno DEMO
cd /d "%~dp0"
if exist "%~dp0..\..\work\ahorra-python" set "PYTHONPATH=%~dp0..\..\work\ahorra-python;%PYTHONPATH%"
echo Ensayo local. No conecta bancos ni proveedores.
echo Abre http://127.0.0.1:8767/ en el navegador.
echo Para cerrar el servidor pulsa Ctrl+C en esta ventana.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m api.sandbox_callback
) else (
  python -m api.sandbox_callback
)
pause
