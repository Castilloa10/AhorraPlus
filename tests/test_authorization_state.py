from concurrent.futures import ThreadPoolExecutor
import unittest
from urllib.parse import parse_qs, urlencode

from api.authorization_state import AuthorizationStates, InvalidReturn, validate_return


class Query:
    def __init__(self, value):
        self.values = parse_qs(value, keep_blank_values=True)

    def getlist(self, key):
        return self.values.get(key, [])

    def get(self, key):
        return self.getlist(key)[-1] if self.getlist(key) else None


class AuthorizationStateTests(unittest.TestCase):
    def test_browser_binding_and_single_use(self):
        states = AuthorizationStates()
        state, browser = states.issue()
        query = Query(urlencode({'state': state, 'code': 'AHORRA-DEMO-ONLY'}))
        with self.assertRaises(InvalidReturn):
            validate_return(query, 'wrong-browser', states)
        self.assertEqual(validate_return(query, browser, states), 'accepted')
        with self.assertRaises(InvalidReturn):
            validate_return(query, browser, states)

    def test_expiry_capacity_and_restart(self):
        now = [0]
        states = AuthorizationStates(clock=lambda: now[0], capacity=1)
        state, browser = states.issue()
        with self.assertRaises(InvalidReturn):
            states.issue()
        now[0] = 300
        with self.assertRaises(InvalidReturn):
            states.consume(state, browser)
        states.issue()
        with self.assertRaises(InvalidReturn):
            AuthorizationStates().consume(state, browser)

    def test_cancellation_error_and_invalid_payloads(self):
        for payload, expected in (({'error': 'access_denied'}, 'cancelled'),
                                  ({'error': 'provider_error'}, 'failed'),
                                  ({'code': 'external-code'}, None),
                                  ({'code': 'AHORRA-DEMO-ONLY', 'error': 'access_denied'}, None),
                                  ({}, None), ({'code': 'x' * 4097}, None)):
            with self.subTest(payload=str(payload)[:80]):
                states = AuthorizationStates()
                state, browser = states.issue()
                query = Query(urlencode({'state': state, **payload}))
                if expected:
                    self.assertEqual(validate_return(query, browser, states), expected)
                else:
                    with self.assertRaises(InvalidReturn):
                        validate_return(query, browser, states)
                with self.assertRaises(InvalidReturn):
                    states.consume(state, browser)

    def test_missing_and_duplicate_parameters(self):
        states = AuthorizationStates()
        state, browser = states.issue()
        for query in ('code=AHORRA-DEMO-ONLY', f'state={state}&state={state}&code=AHORRA-DEMO-ONLY',
                      f'state={state}&code=AHORRA-DEMO-ONLY&code=other'):
            with self.assertRaises(InvalidReturn):
                validate_return(Query(query), browser, states)

    def test_concurrent_returns_only_one_wins(self):
        states = AuthorizationStates()
        state, browser = states.issue()
        def consume(_):
            try:
                states.consume(state, browser)
                return True
            except InvalidReturn:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(consume, range(16))), 1)


try:
    from api import sandbox_callback
    from starlette.requests import Request
except ModuleNotFoundError:
    sandbox_callback = None


@unittest.skipIf(sandbox_callback is None, 'Requiere dependencias de FastAPI')
class CallbackRouteTests(unittest.TestCase):
    def run_middleware(self, path='/', method='GET', origin=None):
        headers = [(b'host', b'127.0.0.1:8767')]
        if origin is not None:
            headers.append((b'origin', origin.encode()))
        request = Request({'type': 'http', 'scheme': 'http', 'path': path, 'method': method,
                           'query_string': b'', 'client': ('127.0.0.1', 1234), 'headers': headers})
        async def handler(request):
            return sandbox_callback.page('DEMO')
        coroutine = sandbox_callback.local_only(request, handler)
        try:
            coroutine.send(None)
        except StopIteration as completed:
            return completed.value
        finally:
            coroutine.close()
        self.fail('El stub no debe realizar operaciones de red')

    def test_form_preserves_origin_but_callback_hides_referrer(self):
        self.assertEqual(self.run_middleware().headers['referrer-policy'], 'same-origin')
        for path in ('/callback', '/result/accepted', '/simulate/accept'):
            self.assertEqual(self.run_middleware(path).headers['referrer-policy'], 'no-referrer')
        self.assertEqual(self.run_middleware('/simulate/accept', 'POST', sandbox_callback.ORIGIN).status_code, 200)
        for origin in (None, 'null', 'https://untrusted.invalid', 'http://127.0.0.1:9999'):
            self.assertEqual(self.run_middleware('/simulate/accept', 'POST', origin).status_code, 403)

    def test_simulated_redirect_cookie_and_clean_final_url(self):
        response = sandbox_callback.simulate('accept')
        self.assertEqual(response.status_code, 303)
        cookie = response.headers['set-cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=lax', cookie)
        query = response.headers['location'].split('?', 1)[1]
        request = Request({'type': 'http', 'method': 'GET', 'path': '/callback',
                           'query_string': query.encode(), 'headers': [(b'cookie', cookie.split(';')[0].encode())]})
        first = sandbox_callback.callback(request)
        self.assertEqual(first.headers['location'], '/result/accepted')
        self.assertIn('Max-Age=0', first.headers['set-cookie'])
        self.assertEqual(sandbox_callback.callback(request).headers['location'], '/result/invalid')

    def test_callback_never_reflects_external_error_or_code(self):
        state, browser = sandbox_callback.states.issue()
        query = urlencode({'state': state, 'error': '<script>alert(1)</script>'})
        request = Request({'type': 'http', 'method': 'GET', 'path': '/callback',
                           'query_string': query.encode(), 'headers': [(b'cookie', f'{sandbox_callback.COOKIE}={browser}'.encode())]})
        response = sandbox_callback.callback(request)
        self.assertEqual(response.headers['location'], '/result/failed')
        self.assertNotIn(b'<script>', sandbox_callback.result('failed').body)
