"""Browser flow for Mock ASPSP only, served on the registered loopback callback."""
import html
import threading
import time
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import HTMLResponse, RedirectResponse

from api.authorization_state import AuthorizationStates, InvalidReturn
from api.sandbox_flow import MockFlow, SandboxError

ORIGIN = 'http://127.0.0.1:8767'
COOKIE = 'ahorra_mock_callback'
states = AuthorizationStates()
lock = threading.Lock()
pending_until = 0
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1'])


def page(content, status=200):
    return HTMLResponse('<!doctype html><html lang="es"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Ahorra+ · Banco ficticio</title><body><main><h1>Banco ficticio · SANDBOX</h1>'
        '<p>Solo Mock ASPSP España. No conecta Openbank ni realiza pagos.</p>' + content + '</main></body></html>', status_code=status)


@app.middleware('http')
async def protect(request, call_next):
    if not request.client or request.client.host != '127.0.0.1' or request.headers.get('host') != '127.0.0.1:8767':
        response = page('<p>Acceso local requerido.</p>', 403)
    elif request.method == 'POST' and request.headers.get('origin') != ORIGIN:
        response = page('<p>Inicia la operación desde la página local.</p>', 403)
    else:
        response = await call_next(request)
    response.headers.update({'Cache-Control': 'no-store', 'Referrer-Policy': 'same-origin' if request.url.path == '/' else 'no-referrer',
        'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self' https://auth.enablebanking.com https://tilisy-sandbox.enablebanking.com"})
    return response


NOTICES = {
    'connected': 'Sesión ficticia autorizada. Ya puedes consultar sus movimientos.',
    'cancelled': 'Autorización cancelada. No se han descargado movimientos.',
    'invalid': 'Retorno no válido, caducado, repetido o recibido desde otro navegador.',
    'failed': 'No se pudo confirmar la operación. No se reintentará automáticamente. Si hay sesión guardada, puedes intentar desconectarla.',
    'downloaded': 'Consulta completa guardada cifrada, separada de Inicio. Si no hay movimientos, hay que preparar datos sintéticos en Mock ASPSP.',
    'disconnected': 'El proveedor ha confirmado la desconexión. La última consulta ficticia se conserva.',
    'busy': 'Ya hay una autorización pendiente. Complétala o espera cinco minutos antes de empezar otra.',
}


@app.get('/')
def index(request: Request):
    flow = MockFlow()
    notice = NOTICES.get(request.query_params.get('notice'), '')
    try:
        session, snapshot = flow.session(), flow.snapshot()
    except Exception:
        return page('<p>No se pudo abrir el almacén cifrado.</p>', 503)
    body = '<p role="status">' + html.escape(notice) + '</p>'
    if session:
        body += '<p>Hay una sesión de pruebas guardada. Su vigencia se verifica al consultar.</p>'
        body += '<form method="post" action="/download"><button>Consultar cuentas y movimientos ficticios</button></form>'
        body += '<form method="post" action="/disconnect"><label><input type="checkbox" name="confirm" value="disconnect" required> Quiero desconectar la sesión de pruebas; conservar la última consulta.</label><button>Desconectar del proveedor de pruebas</button></form>'
    else:
        body += '<h2>Autorizar el ensayo</h2><p>Proveedor: Enable Banking. Banco: Mock ASPSP España. Solo lectura de cuentas, saldos y movimientos ficticios disponibles. Duración solicitada: como máximo una hora. La información pasará por el proveedor y se guardará cifrada en este PC, separada de tus datos de Inicio.</p>'
        body += '<p>Continúa en este mismo navegador y vuelve aquí tras autorizar. Si el proveedor presenta condiciones, revísalas antes de aceptar. No introduzcas datos reales en el banco simulado.</p>'
        body += '<form method="post" action="/begin"><label><input type="checkbox" name="confirm" value="mock-only" required> Quiero iniciar únicamente el ensayo con datos ficticios.</label><button>Ir a autorizar Mock ASPSP</button></form>'
    if snapshot:
        body += '<h2>Última consulta ficticia</h2><p>' + html.escape(snapshot['downloaded_at']) + '</p>'
        for account in snapshot['accounts']:
            body += '<h3>' + html.escape(str(account['name'])) + '</h3>'
            for balance in account['balances']:
                amount = balance.get('balance_amount') or {}
                body += '<p>Saldo comunicado por el banco ficticio: ' + html.escape(str(amount.get('amount', '')) + ' ' + str(amount.get('currency', '')) + ' · ' + str(balance.get('balance_type', ''))) + '</p>'
            body += '<p>Movimientos recibidos: ' + str(len(account['transactions'])) + '. No se suman al saldo de Inicio.</p><ul>'
            for row in account['transactions'][:100]:
                amount = row.get('transaction_amount') or {}
                lines = row.get('remittance_information') or []
                description = ' '.join(str(line) for line in lines) if isinstance(lines, list) else str(lines)
                text = f"{row.get('booking_date', 'Sin fecha')} · {description} · {row.get('credit_debit_indicator', '')} {amount.get('amount', '')} {amount.get('currency', '')} · {row.get('status', '')}"
                body += '<li>' + html.escape(text) + '</li>'
            body += '</ul>'
            if len(account['transactions']) > 100:
                body += '<p>Se muestran los primeros 100; la consulta completa está guardada.</p>'
        if not snapshot['accounts']:
            body += '<p>El banco ficticio no devolvió cuentas.</p>'
    return page(body)


def redirect(notice):
    return RedirectResponse('/?notice=' + notice, status_code=303)


async def confirmed(request, value):
    if request.headers.get('content-length', '').isdigit() and int(request.headers['content-length']) > 1024:
        return False
    body = await request.body()
    if len(body) > 1024:
        return False
    return parse_qs(body.decode('utf-8', errors='replace')).get('confirm') == [value]


def start():
    global pending_until
    with lock:
        if pending_until > time.monotonic():
            return redirect('busy')
        state, browser = states.issue()
        try:
            url = MockFlow().begin(state)
        except Exception:
            states.consume(state, browser)
            return redirect('failed')
        pending_until = time.monotonic() + 300
        response = RedirectResponse(url, status_code=303)
        response.set_cookie(COOKIE, browser, max_age=300, httponly=True, samesite='lax', path='/callback')
        return response


@app.post('/begin')
async def begin(request: Request):
    if not await confirmed(request, 'mock-only'):
        return page('<p>Marca la confirmación del ensayo.</p><a href="/">Volver</a>', 400)
    return await run_in_threadpool(start)


@app.get('/callback')
def callback(request: Request):
    global pending_until
    query = request.query_params
    try:
        if any(len(query.getlist(name)) > 1 for name in ('state', 'code', 'error')):
            raise InvalidReturn()
        states.consume(query.get('state'), request.cookies.get(COOKIE))
    except InvalidReturn:
        return redirect('invalid')
    with lock:
        pending_until = 0
        code, error = query.get('code'), query.get('error')
        if bool(code) == bool(error):
            notice = 'invalid'
        elif error:
            notice = 'cancelled' if error == 'access_denied' else 'failed'
        else:
            try:
                MockFlow().finish(code)
                notice = 'connected'
            except Exception:
                notice = 'failed'
    response = redirect(notice)
    response.delete_cookie(COOKIE, path='/callback', httponly=True, samesite='lax')
    return response


@app.post('/download')
def download():
    with lock:
        try:
            MockFlow().download()
            return redirect('downloaded')
        except Exception:
            return redirect('failed')


def revoke():
    with lock:
        try:
            MockFlow().disconnect()
            return redirect('disconnected')
        except Exception:
            return redirect('failed')


@app.post('/disconnect')
async def disconnect(request: Request):
    if not await confirmed(request, 'disconnect'):
        return page('<p>Confirma la desconexión del ensayo.</p><a href="/">Volver</a>', 400)
    return await run_in_threadpool(revoke)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8767, access_log=False, log_level='warning')
