"""Import an explicitly selected test key without exposing it in output."""
import argparse
from contextlib import closing
from pathlib import Path
from uuid import UUID

from api.storage import connect
from api.sandbox_probe import VAULT, SandboxError


def configure(source, app_id, database=VAULT):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
    try:
        app_id = str(UUID(app_id))
        with Path(source).open('rb') as stream:
            content = stream.read(16385)
        if len(content) > 16384:
            raise ValueError()
        key = load_pem_private_key(content, password=None)
        if not isinstance(key, RSAPrivateKey) or key.key_size < 2048:
            raise ValueError()
        private_key = content.decode('ascii')
    except (ValueError, TypeError, OSError, UnicodeError):
        raise SandboxError('No se pudo validar el archivo de clave RSA de pruebas') from None
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(database)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS local_secrets (name TEXT PRIMARY KEY, value TEXT NOT NULL)')
        existing = dict(db.execute('SELECT name, value FROM local_secrets'))
        desired = {'provider_app_id': app_id, 'provider_private_key': private_key}
        if any(name in existing and existing[name] != value for name, value in desired.items()):
            raise SandboxError('Ya existe otra configuración protegida; no se ha sobrescrito')
        for name, value in desired.items():
            db.execute('INSERT OR IGNORE INTO local_secrets VALUES (?, ?)', (name, value))
    # Source remains untouched: deleting the original is a separate user decision.


def main():
    parser = argparse.ArgumentParser(description='Guardar cifrada una clave de aplicación Sandbox')
    parser.add_argument('--archivo', type=Path, required=True)
    parser.add_argument('--aplicacion', required=True)
    args = parser.parse_args()
    try:
        configure(args.archivo, args.aplicacion)
        print('Configuración cifrada guardada. El archivo original sigue en su ubicación. Sin consultas externas.')
        return 0
    except Exception:
        print('No se pudo guardar la configuración. No se muestran detalles de la clave.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
