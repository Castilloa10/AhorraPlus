"""Explicit, read-only SANDBOX handshake. No bank authorisation or account access."""
import argparse
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID

from api.privacy import load_secret

BASE_URL = 'https://api.enablebanking.com'
VAULT = Path(__file__).resolve().parents[1] / '.local' / 'sandbox.sqlite3'


class SandboxError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SandboxError('El proveedor devolvió una redirección inesperada')


def sign_token(app_id, private_key):
    try:
        import jwt
        now = int(time.time())
        return jwt.encode(
            {'iss': 'enablebanking.com', 'aud': 'api.enablebanking.com', 'iat': now, 'exp': now + 300},
            private_key, algorithm='RS256', headers={'kid': app_id, 'typ': 'JWT'},
        )
    except ImportError:
        raise SandboxError('Falta instalar requirements-sandbox.txt') from None
    except Exception:
        raise SandboxError('No se pudo firmar la petición de prueba') from None


def get_json(path, token):
    # Deliberately allow only these two non-financial GET operations.
    if path not in ('/application', '/aspsps?country=ES'):
        raise SandboxError('Operación no permitida en esta comprobación')
    request = Request(BASE_URL + path, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            content = response.read(2_000_001)
            if len(content) > 2_000_000:
                raise SandboxError('Respuesta demasiado grande')
            result = json.loads(content)
            if not isinstance(result, dict):
                raise SandboxError('Respuesta no válida')
            return result
    except HTTPError as error:
        # Do not expose response bodies, request headers or keys in diagnostics.
        raise SandboxError(f'El proveedor respondió con estado HTTP {error.code}') from None
    except (URLError, TimeoutError, OSError):
        raise SandboxError('No se pudo contactar con el proveedor; no se ha conectado ningún banco') from None
    except (ValueError, UnicodeError):
        raise SandboxError('Respuesta no válida del proveedor') from None


def probe(app_id, private_key, *, transport=get_json, signer=sign_token):
    try:
        app_id = str(UUID(app_id))
    except (ValueError, TypeError, AttributeError):
        raise SandboxError('Falta un identificador válido de aplicación de pruebas') from None
    if not private_key:
        raise SandboxError('Falta la clave protegida de la aplicación de pruebas')
    token = signer(app_id, private_key)
    application = transport('/application', token)
    if application.get('environment') != 'SANDBOX':
        raise SandboxError('Bloqueado: la aplicación no está confirmada como SANDBOX')
    if application.get('kid') != app_id or application.get('active') is not True:
        raise SandboxError('La aplicación de pruebas no coincide o no está activa')
    if 'AIS' not in application.get('services', []):
        raise SandboxError('La aplicación no admite información de cuentas')
    catalog = transport('/aspsps?country=ES', token)
    banks = catalog.get('aspsps')
    if not isinstance(banks, list) or any(not isinstance(bank, dict) for bank in banks):
        raise SandboxError('Catálogo de pruebas no válido')
    # Return public catalogue fields only; never output sandbox credential objects.
    return {'environment': 'SANDBOX', 'banks': [
        {'name': bank.get('name'), 'country': bank.get('country')} for bank in banks
    ], 'bank_connected': False}


def main():
    parser = argparse.ArgumentParser(description='Comprobación de Enable Banking SANDBOX, sin conectar bancos')
    parser.add_argument('--consultar-proveedor', action='store_true', help='Realiza dos consultas HTTPS al proveedor si hay configuración')
    args = parser.parse_args()
    if not args.consultar_proveedor:
        print('Modo desconectado. No se ha realizado ninguna petición. Lee SANDBOX.md antes de configurar.')
        return 0
    try:
        result = probe(os.getenv('AHORRA_SANDBOX_APP_ID') or load_secret(VAULT, 'provider_app_id'),
                       load_secret(VAULT, 'provider_private_key'))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except SandboxError as error:
        print(str(error))
        return 1
    except Exception:
        print('No se pudo abrir la configuración protegida. No se muestran detalles privados.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
