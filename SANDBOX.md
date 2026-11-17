# Pruebas con banco ficticio

Módulo opcional y experimental. Inicio funciona con datos DEMO sin registrarse en ningún proveedor. La autorización, descarga y desconexión completas con el proveedor aún están pendientes de verificar.

## Alcance

Admite exclusivamente Mock ASPSP España en el entorno SANDBOX de Enable Banking. Comprueba la aplicación y AIS antes de operar. No admite producción ni pagos. El permiso solicitado dura como máximo una hora; el estado de retorno caduca a los cinco minutos y está vinculado al mismo navegador.

El servidor escucha en http://127.0.0.1:8767/ y recibe el retorno en http://127.0.0.1:8767/callback. Los destinos de autorización permitidos son auth.enablebanking.com y tilisy-sandbox.enablebanking.com mediante HTTPS.

## Configuración propia

Esta copia no incluye claves, identificadores de aplicación, sesiones ni bases de datos. Para experimentar se necesita una aplicación SANDBOX propia con el retorno anterior, revisar las condiciones del proveedor e instalar requirements-sandbox.txt. Consulta las opciones con `python -m api.sandbox_config --help`. No uses datos reales ni publiques la clave privada.

Con las dependencias y configuración preparadas, abre `Conectar banco ficticio.cmd`. Confirma el alcance de prueba y completa el recorrido en el mismo navegador. La descarga requiere pulsar su botón y no modifica el saldo de Inicio.

Claves, sesiones y descargas se guardan cifradas para el usuario de Windows en .local/sandbox.sqlite3. Desconectar solicita primero la revocación remota; elimina la sesión local solo tras confirmación, conservando la clave y última descarga. El control de privacidad de Inicio solo afecta a la simulación local.

Si el intercambio se interrumpe, el resultado remoto puede ser incierto: revisa el permiso en el portal del proveedor. No hay recuperación automática de todos los fallos. No es una integración apta para datos financieros reales.

## Ensayo sin proveedor

`Probar retorno DEMO.cmd` simula aceptación y cancelación sin conectar servicios. Utiliza el mismo puerto; no ejecutes ambos servidores simultáneamente.

## Referencias

- https://enablebanking.com/docs/api/quick-start/
- https://enablebanking.com/docs/api/sandbox/
- https://enablebanking.com/docs/api/reference/

Consulta PRIVACIDAD.md para los límites del cifrado local.
