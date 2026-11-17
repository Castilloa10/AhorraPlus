import unittest

try:
    from api.main import local_access, allowed_origins
    from starlette.requests import Request
    from starlette.responses import Response
except ModuleNotFoundError:
    local_access = None


@unittest.skipIf(local_access is None, 'Instala requirements.txt para probar la API')
class AccessTests(unittest.TestCase):
    def check_request(self, method, origin=None, host='127.0.0.1'):
        headers = [] if origin is None else [(b'origin', origin.encode())]
        request = Request({'type': 'http', 'method': method, 'headers': headers,
                           'client': (host, 1234), 'path': '/'})
        async def next_handler(request):
            return Response('ok')
        coroutine = local_access(request, next_handler)
        try:
            coroutine.send(None)
        except StopIteration as completed:
            return completed.value
        finally:
            coroutine.close()
        self.fail('El stub no debe realizar operaciones de red')

    def test_foreign_origin_missing_origin_and_remote_client_rejected(self):
        for method in ('GET', 'POST'):
            self.assertEqual(self.check_request(method, 'https://untrusted.invalid').status_code, 403)
        self.assertEqual(self.check_request('POST').status_code, 403)
        self.assertEqual(self.check_request('GET', host='192.168.1.2').status_code, 403)

    def test_local_browser_allowed_without_caching(self):
        response = self.check_request('POST', allowed_origins[0])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(self.check_request('GET').status_code, 200)
