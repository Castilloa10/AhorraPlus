"""Allowlisted Mock ASPSP client. Never writes to the main DEMO database."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener
from uuid import UUID

from api.privacy import load_secret, store_secret
from api.sandbox_probe import BASE_URL, VAULT, NoRedirect, SandboxError, sign_token
from api.storage import connect

CALLBACK = 'http://127.0.0.1:8767/callback'
MOCK = {'name': 'Mock ASPSP', 'country': 'ES'}
AUTH_HOSTS = frozenset({'auth.enablebanking.com', 'tilisy-sandbox.enablebanking.com'})


def identifier(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise SandboxError('Identificador de pruebas no válido') from None


def transport(method, path, token, payload=None):
    route = urlsplit(path)
    allowed = ((method, route.path) in {('GET', '/application'), ('GET', '/aspsps'), ('POST', '/auth'), ('POST', '/sessions')}
               or (method in ('GET', 'DELETE') and re.fullmatch(r'/sessions/[a-f0-9-]{36}', route.path))
               or (method == 'GET' and re.fullmatch(r'/accounts/[a-f0-9-]{36}/(balances|transactions)', route.path)))
    if not allowed or route.scheme or route.netloc or route.fragment:
        raise SandboxError('Operación no permitida')
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(BASE_URL + path, data=data, method=method,
                      headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise SandboxError('Respuesta de pruebas demasiado grande')
            result = json.loads(raw) if raw else {}
            if not isinstance(result, dict):
                raise SandboxError('Respuesta de pruebas no válida')
            return result
    except HTTPError as error:
        raise SandboxError(f'El proveedor devolvió HTTP {error.code}. No se ha confirmado la operación.') from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise SandboxError('No se pudo confirmar la respuesta del proveedor. No se reintentará automáticamente.') from None


class MockClient:
    def __init__(self, app_id, key, *, sender=transport, signer=sign_token):
        self.app_id, self.key = identifier(app_id), key
        self.sender, self.signer, self.verified = sender, signer, False

    def call(self, method, path, payload=None):
        token = self.signer(self.app_id, self.key)
        if not self.verified:
            app = self.sender('GET', '/application', token, None)
            if (app.get('environment') != 'SANDBOX' or app.get('kid') != self.app_id
                    or app.get('active') is not True or 'AIS' not in (app.get('services') or [])
                    or CALLBACK not in (app.get('redirect_urls') or [])):
                raise SandboxError('La aplicación debe ser SANDBOX activa, coincidente, con AIS y el retorno registrado')
            self.verified = True
        return self.sender(method, path, token, payload)

    def begin(self, state):
        catalog = self.call('GET', '/aspsps?country=ES')
        matches = [item for item in catalog.get('aspsps', []) if item.get('name') == MOCK['name'] and item.get('country') == 'ES']
        if len(matches) != 1:
            raise SandboxError('Mock ASPSP no está disponible')
        maximum = matches[0].get('maximum_consent_validity')
        if not isinstance(maximum, int) or maximum < 60:
            raise SandboxError('No se pudo verificar la duración permitida')
        expires = datetime.now(timezone.utc) + timedelta(seconds=min(maximum, 3600))
        result = self.call('POST', '/auth', {'aspsp': MOCK, 'state': state, 'redirect_url': CALLBACK,
                          'psu_type': 'personal', 'language': 'es', 'access': {'valid_until': expires.isoformat()}})
        url = result.get('url', '')
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname not in AUTH_HOSTS or parsed.port not in (None, 443) or parsed.username or parsed.password:
            raise SandboxError('Dirección de autorización no admitida')
        return url

    def exchange(self, code):
        if not isinstance(code, str) or not 1 <= len(code) <= 4096:
            raise SandboxError('Código de pruebas no válido')
        return self.call('POST', '/sessions', {'code': code})


def validate_session(session):
    if session.get('aspsp') != MOCK:
        raise SandboxError('La sesión no pertenece a Mock ASPSP España')
    identifier(session.get('session_id'))
    accounts = session.get('accounts')
    if not isinstance(accounts, list) or len(accounts) > 20:
        raise SandboxError('Lista de cuentas de prueba no válida')
    seen = set()
    for account in accounts:
        uid = identifier(account.get('uid'))
        if uid in seen:
            raise SandboxError('Cuenta de prueba repetida')
        seen.add(uid)
    try:
        expiry = datetime.fromisoformat(session['access']['valid_until'].replace('Z', '+00:00'))
        if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
            raise ValueError()
    except (ValueError, KeyError, TypeError, AttributeError):
        raise SandboxError('Sesión de pruebas caducada o sin fecha válida') from None
    return accounts


class MockFlow:
    def __init__(self, database=VAULT, client=None):
        self.database = database
        self.client = client

    def provider(self):
        if self.client is None:
            self.client = MockClient(load_secret(self.database, 'provider_app_id'), load_secret(self.database, 'provider_private_key'))
        return self.client

    def session(self):
        saved = load_secret(self.database, 'bank_session')
        return json.loads(saved) if saved else None

    def begin(self, state):
        if self.session():
            raise SandboxError('Ya hay una sesión guardada. Desconéctala antes de autorizar otra.')
        return self.provider().begin(state)

    def finish(self, code):
        if self.session():
            raise SandboxError('Ya hay una sesión guardada. No se creará otra.')
        session = self.provider().exchange(code)
        # Persist its ID before validation so a malformed response can still be revoked.
        identifier(session.get('session_id'))
        store_secret(self.database, 'bank_session', json.dumps(session))
        validate_session(session)

    def snapshot(self):
        if not self.database.exists():
            return None
        with closing(connect(self.database)) as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='sandbox_snapshot'").fetchone():
                return None
            row = db.execute('SELECT content FROM sandbox_snapshot WHERE id=1').fetchone()
            return json.loads(row[0]) if row else None

    def download(self):
        session = self.session()
        if not session:
            raise SandboxError('No hay una sesión de pruebas')
        accounts = validate_session(session)
        provider = self.provider()
        current = provider.call('GET', '/sessions/' + identifier(session['session_id']))
        if current.get('status') != 'AUTHORIZED' or current.get('aspsp') != MOCK:
            raise SandboxError('El proveedor ya no confirma una sesión Mock autorizada')
        output = []
        for account in accounts:
            uid = identifier(account['uid'])
            if uid not in current.get('accounts', []):
                raise SandboxError('La cuenta ya no está autorizada')
            base = '/accounts/' + uid
            balances = provider.call('GET', base + '/balances').get('balances')
            if not isinstance(balances, list):
                raise SandboxError('Saldos de prueba no válidos')
            transactions, cursor, seen = [], None, set()
            for _ in range(100):
                path = base + '/transactions' + ('?' + urlencode({'continuation_key': cursor}) if cursor else '')
                page = provider.call('GET', path)
                rows = page.get('transactions')
                if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                    raise SandboxError('Página de movimientos no válida')
                transactions.extend(rows)
                if len(transactions) > 10000:
                    raise SandboxError('Se superó el límite del ensayo; no se guarda una descarga parcial')
                cursor = page.get('continuation_key')
                if cursor is None or cursor == '':
                    break
                if not isinstance(cursor, str) or len(cursor) > 4096 or cursor in seen:
                    raise SandboxError('Paginación repetida o inválida; no se guarda una descarga parcial')
                seen.add(cursor)
            else:
                raise SandboxError('Se superó el límite de páginas; no se guarda una descarga parcial')
            output.append({'name': account.get('name') or 'Cuenta ficticia', 'currency': account.get('currency'),
                           'balances': balances, 'transactions': transactions})
        snapshot = {'demo': True, 'provider': MOCK, 'downloaded_at': datetime.now(timezone.utc).isoformat(), 'accounts': output}
        with closing(connect(self.database)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS sandbox_snapshot (id INTEGER PRIMARY KEY, content TEXT NOT NULL)')
            db.execute('INSERT INTO sandbox_snapshot VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET content=excluded.content', (json.dumps(snapshot),))
        return snapshot

    def disconnect(self):
        session = self.session()
        if not session:
            return
        self.provider().call('DELETE', '/sessions/' + identifier(session['session_id']))
        # Keep the session on any remote failure so revocation can be retried.
        with closing(connect(self.database)) as db, db:
            db.execute("DELETE FROM local_secrets WHERE name='bank_session'")
