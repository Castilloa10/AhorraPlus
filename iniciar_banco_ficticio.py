"""Release only the positively identified old callback rehearsal, then start Mock UI."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

# Run by the user's launcher. Do not stop any listener with another command line.
CHECK_OLD = r'''
$ErrorActionPreference = 'Stop'
$listeners = @(Get-NetTCPConnection -LocalPort 8767 -State Listen -ErrorAction SilentlyContinue)
if ($listeners.Count -eq 0) { exit 0 }
$owners = @($listeners.OwningProcess | Select-Object -Unique)
if ($owners.Count -ne 1) { exit 2 }
$oldProcess = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $owners[0])
if ($oldProcess.Name -notin @('python.exe', 'pythonw.exe')) { exit 2 }
if ($oldProcess.CommandLine -notmatch '(?:^|\s)-m\s+api\.(?:sandbox_callback|sandbox_live)\s*$') { exit 2 }
Stop-Process -Id $oldProcess.ProcessId -ErrorAction Stop
Wait-Process -Id $oldProcess.ProcessId -Timeout 5 -ErrorAction SilentlyContinue
exit 0
'''


def main():
    if os.name != 'nt':
        print('Este lanzador requiere Windows.')
        return 1
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', CHECK_OLD],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode != 0:
        print('No se ha cerrado ningun programa: el puerto 8767 esta ocupado por otro proceso o no se pudo identificar.')
        print('No se pudo reiniciar el ensayo de forma segura. Cierra su ventana y vuelve a intentarlo.')
        return 1
    print('Banco ficticio SANDBOX: abre http://127.0.0.1:8767/')
    print('Deja esta ventana abierta. Pulsa Ctrl+C para detener el servidor.')
    try:
        return subprocess.call([sys.executable, '-m', 'api.sandbox_live'], cwd=ROOT)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
