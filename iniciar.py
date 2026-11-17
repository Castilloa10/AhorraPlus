"""Start the local demo with existing dependencies and automatically chosen ports."""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import build_opener, ProxyHandler
import webbrowser

ROOT = Path(__file__).resolve().parent


def configuration():
    from api.protection import transform
    probe = b'Ahorra+ synthetic protection check'
    if transform(transform(probe), decrypt=True) != probe:
        raise RuntimeError('No se pudo comprobar la protección de Windows')
    environment = os.environ.copy()
    local_packages = ROOT.parent.parent / "work" / "ahorra-python"
    if local_packages.is_dir():
        sys.path.insert(0, str(local_packages))
        environment["PYTHONPATH"] = str(local_packages) + os.pathsep + environment.get("PYTHONPATH", "")
    missing = [name for name in ("uvicorn", "fastapi") if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError("Faltan las dependencias de Python. Sigue el apartado API local del README.")
    node = shutil.which("node")
    cli = ROOT / "app" / "node_modules" / "expo" / "bin" / "cli"
    if not node or not cli.is_file():
        raise RuntimeError("Faltan Node.js o las dependencias de la app. Sigue el apartado Windows del README.")
    return environment, node, cli


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_ready(url, processes, timeout):
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise RuntimeError("Un servicio se ha detenido durante el arranque. Consulta los registros indicados.")
        try:
            with opener.open(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    raise RuntimeError("El arranque ha tardado demasiado. Consulta los registros indicados y vuelve a intentarlo.")


def stop(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main():
    parser = argparse.ArgumentParser(description="Abrir Ahorra+ en este ordenador")
    parser.add_argument("--check", action="store_true", help="Comprobar dependencias sin arrancar servicios")
    args = parser.parse_args()
    processes = []
    logs = []
    try:
        environment, node, cli = configuration()
        if args.check:
            print("Python, FastAPI, Uvicorn, Node.js y Expo disponibles. Protección de Windows comprobada.")
            return 0
        api_port = free_port()
        web_port = free_port()
        while web_port == api_port:
            web_port = free_port()
        api_url = f"http://127.0.0.1:{api_port}"
        web_url = f"http://127.0.0.1:{web_port}"
        environment["AHORRA_WEB_ORIGINS"] = web_url
        environment["EXPO_PUBLIC_API_URL"] = api_url
        environment["CI"] = "1"
        environment["EXPO_OFFLINE"] = "1"
        environment["EXPO_NO_TELEMETRY"] = "1"
        environment["BROWSER"] = "none"
        log_directory = ROOT / ".local"
        log_directory.mkdir(exist_ok=True)
        print("Preparando Ahorra+ DEMO. El primer arranque puede tardar un minuto.")
        print(f"Registros de arranque: {log_directory}")
        commands = [
            ("api", [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", str(api_port)], ROOT),
            ("web", [node, str(cli), "start", "--web", "--clear", "--port", str(web_port), "--localhost"], ROOT / "app"),
        ]
        for name, command, directory in commands:
            log = (log_directory / f"{name}-{api_port}.log").open("w", encoding="utf-8")
            logs.append(log)
            processes.append(subprocess.Popen(
                command, cwd=directory, env=environment, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            ))
        wait_ready(api_url + "/api/v1/demo/home", processes, 30)
        wait_ready(web_url, processes, 120)
        print(f"Pagina lista: {web_url}")
        webbrowser.open(web_url)
        input("Deja esta ventana abierta mientras usas Ahorra+. Pulsa INTRO aqui para apagarla.\n")
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(f"No se pudo iniciar Ahorra+: {error}")
        return 1
    finally:
        for process in reversed(processes):
            stop(process)
        for log in logs:
            log.close()


if __name__ == "__main__":
    sys.exit(main())
