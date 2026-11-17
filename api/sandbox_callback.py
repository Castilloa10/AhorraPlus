"""Separate local callback rehearsal; no provider transport or financial storage."""
from urllib.parse import urlencode

from fastapi import FastAPI, Request
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import HTMLResponse, RedirectResponse

from api.authorization_state import AuthorizationStates, InvalidReturn, validate_return

ORIGIN = 'http://127.0.0.1:8767'
CALLBACK_URL = ORIGIN + '/callback'
COOKIE = 'ahorra_callback_demo'
states = AuthorizationStates()
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1'])


def page(message, status=200):
    # All messages are fixed application text, never supplied by the callback.
    return HTMLResponse('<!doctype html><html lang="es"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Ahorra+ · Retorno de prueba</title><body><main>'
        '<h1>Retorno de autorización · DEMO</h1><p>Sin banco ni proveedor conectado.</p>'
        f'<p>{message}</p><a href="/">Volver al ensayo</a></main></body></html>', status_code=status)


@app.middleware('http')
async def local_only(request, call_next):
    if (not request.client or request.client.host != '127.0.0.1'
            or request.headers.get('host') != '127.0.0.1:8767'):
        return page('Acceso local requerido.', 403)
    if request.method == 'POST' and request.headers.get('origin') != ORIGIN:
        return page('Inicia el ensayo desde su página local.', 403)
    response = await call_next(request)
    response.headers.update({
        'Cache-Control': 'no-store',
        # The form needs its same-origin Origin header on POST. Never forward
        # the callback query to subsequent pages or any external destination.
        'Referrer-Policy': 'same-origin' if request.url.path == '/' else 'no-referrer',
        'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    })
    return response


@app.get('/')
def index():
    return page('Ensayo independiente. Caduca en cinco minutos y requiere el mismo navegador. '
                'No guarda movimientos ni concede permisos.'
                '<form method="post" action="/simulate/accept"><button>Probar retorno aceptado</button></form>'
                '<form method="post" action="/simulate/cancel"><button>Probar cancelación</button></form>')


@app.post('/simulate/{outcome}')
def simulate(outcome: str):
    if outcome not in ('accept', 'cancel'):
        return page('Ensayo no reconocido.', 400)
    try:
        state, browser = states.issue()
    except InvalidReturn:
        return page('Hay demasiados ensayos pendientes. Espera cinco minutos.', 429)
    query = {'state': state}
    query.update({'code': 'AHORRA-DEMO-ONLY'} if outcome == 'accept' else {'error': 'access_denied'})
    response = RedirectResponse('/callback?' + urlencode(query), status_code=303)
    # HTTP loopback only; Secure cookies require HTTPS in the future production flow.
    response.set_cookie(COOKIE, browser, max_age=300, httponly=True, samesite='lax', path='/callback')
    return response


@app.get('/callback')
def callback(request: Request):
    try:
        outcome = validate_return(request.query_params, request.cookies.get(COOKIE), states)
    except InvalidReturn:
        outcome = 'invalid'
    # Strip code and state from the final address and never echo provider content.
    response = RedirectResponse('/result/' + outcome, status_code=303)
    response.delete_cookie(COOKIE, path='/callback', httponly=True, samesite='lax')
    return response


@app.get('/result/{outcome}')
def result(outcome: str):
    messages = {
        'accepted': 'Retorno ficticio comprobado. No se ha creado ninguna sesión bancaria.',
        'cancelled': 'Ensayo cancelado. No se ha concedido ningún permiso.',
        'failed': 'El ensayo devolvió un error. Inicia una nueva prueba.',
        'invalid': 'Retorno rechazado: solicitud desconocida, caducada, repetida o de otro navegador.',
    }
    # Informational result pages confer no permission, including when opened directly.
    return page(messages.get(outcome, 'Resultado de ensayo desconocido.'), 200 if outcome in messages else 404)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8767, access_log=False, log_level='warning')
