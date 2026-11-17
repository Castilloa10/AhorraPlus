"""Short-lived, browser-bound one-use state for local authorization rehearsals."""
from dataclasses import dataclass
import hashlib
import secrets
import threading
import time


class InvalidReturn(ValueError):
    pass


@dataclass
class Pending:
    browser_hash: str
    expires: float


class AuthorizationStates:
    def __init__(self, *, clock=time.monotonic, ttl=300, capacity=100):
        self.clock, self.ttl, self.capacity = clock, ttl, capacity
        self._pending = {}
        self._lock = threading.Lock()

    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    def issue(self):
        with self._lock:
            now = self.clock()
            self._pending = {key: value for key, value in self._pending.items() if value.expires > now}
            if len(self._pending) >= self.capacity:
                raise InvalidReturn('Hay demasiados ensayos pendientes. Espera cinco minutos.')
            state, browser = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            self._pending[self.digest(state)] = Pending(self.digest(browser), now + self.ttl)
            return state, browser

    def consume(self, state, browser):
        if not isinstance(state, str) or not isinstance(browser, str) or not (1 <= len(state) <= 128 and 1 <= len(browser) <= 128):
            raise InvalidReturn('Retorno de prueba no válido o caducado')
        with self._lock:
            key = self.digest(state)
            pending = self._pending.get(key)
            if pending is None:
                raise InvalidReturn('Retorno de prueba no válido o caducado')
            if pending.expires <= self.clock():
                del self._pending[key]
                raise InvalidReturn('Retorno de prueba no válido o caducado')
            if not secrets.compare_digest(pending.browser_hash, self.digest(browser)):
                raise InvalidReturn('Retorno de prueba no válido o caducado')
            del self._pending[key]


def validate_return(query, browser, states):
    """Accept exactly one state and either a code or an error; consume once."""
    for field in ('state', 'code', 'error'):
        if len(query.getlist(field)) > 1:
            raise InvalidReturn('Parámetros duplicados en el retorno de prueba')
    state, code, error = query.get('state'), query.get('code'), query.get('error')
    states.consume(state, browser)
    if bool(code) == bool(error) or (code and len(code) > 4096) or (error and len(error) > 256):
        raise InvalidReturn('Respuesta de autorización de prueba no válida')
    if error:
        return 'cancelled' if error == 'access_denied' else 'failed'
    # This milestone accepts only a fixed synthetic code, never a provider code.
    if code != 'AHORRA-DEMO-ONLY':
        raise InvalidReturn('Esta versión solo admite códigos ficticios de ensayo')
    return 'accepted'
