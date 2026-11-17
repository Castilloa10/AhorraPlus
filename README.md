# Ahorra+

Prototipo de gestor financiero personal con Expo / React Native Web y Python / FastAPI. Usa datos ficticios. No está preparado para conectar cuentas bancarias reales.

El guardado cifrado requiere Windows. La interfaz DEMO puede probarse en web, iOS y Android; la importación de archivos solo está implementada para web. No incluye servicios de pago ni APIs de IA.

## Proveedor de pruebas opcional

Existe un recorrido separado para Mock ASPSP con Enable Banking. Su validación completa con el proveedor sigue pendiente. Esta distribución no incluye credenciales ni sesiones. Consulta SANDBOX.md.

## Ensayo del consentimiento bancario

El bloque «Permiso bancario de prueba» permite revisar el alcance propuesto, marcar una casilla inicialmente desmarcada y simular la autorización. También permite cancelar o simular la desconexión con confirmación. No hace peticiones al banco ni al proveedor, no guarda permisos, no importa datos y no modifica movimientos ni saldos. Su estado vive solo en la pantalla y se reinicia al recargar. Está disponible también sin API. Las cuentas, el historial y la duración de un futuro permiso real quedan pendientes de acordar; esta pantalla no constituye consentimiento bancario ni aceptación de contratos.

## Protección local de la DEMO

El guardado usa cifrado vinculado a tu usuario de Windows. Cierra todas las APIs antiguas antes de abrir esta versión; convertirá el archivo existente al leerlo. Inicio incorpora controles para desconectar la autorización local de prueba y borrar los movimientos importados con confirmación. Lee [activación, recuperación y límites](PRIVACIDAD.md). Sigue sin estar habilitada la conexión bancaria real.

## Simulación bancaria local

En Importar movimientos DEMO, pulsa Cargar simulación bancaria. La vista previa muestra una compra ficticia de 30 € y un abono ficticio de 10 €. Confirmar importación los añade a la cuenta DEMO importada, con efecto neto de −20 €. Cancelar descarta la vista previa. Repetir la importación añade cero movimientos. Los conceptos aparecen Sin categoría para asignarlos manualmente.

La simulación se ejecuta con un archivo local inspirado en el formato del proveedor. La integración externa y la autorización bancaria quedan pendientes. Consulta [la revisión de conexión y protección de datos](CONEXION_BANCARIA.md) para las decisiones que debemos acordar antes de conectar una cuenta real.

## Gastos fijos e irregulares

Inicio permite añadir y editar cargos pendientes con nombre, importe positivo, tipo y fecha prevista. Cada entrada representa un único cargo. La repetición automática y la conciliación con movimientos importados quedan pendientes. Los cargos vencidos y los previstos hasta fin del mes del resumen se incluyen en pagos comprometidos. Un cargo posterior queda guardado para su fecha. Guardar recalcula el disponible. La muestra mantiene el corte del 14 de noviembre de 2026.

## Presupuestos mensuales

Inicio muestra presupuestos de la cuenta DEMO importada para el mes de su fecha de corte, actualmente noviembre de 2026. Pulsa Fijar presupuesto en una categoría de gasto, introduce el límite en euros y confirma. Admite coma o punto decimal, hasta dos decimales y valores desde 0 hasta 1.000.000 €. Un límite de 0 es un presupuesto válido. Los límites empiezan sin definir.

El gasto neto suma los cargos del mes y descuenta los abonos de esa misma categoría, con mínimo cero. El restante es el límite menos el gasto y puede indicar un exceso. Cambiar la categoría de un movimiento recalcula el gasto. Solo se consideran movimientos importados hasta la fecha del resumen. Los límites se guardan por mes y categoría. El selector de otros meses queda pendiente. El saldo disponible sigue calculándose con el saldo, los pagos comprometidos y el ahorro protegido.

## Categorías de movimientos

En Inicio, cada movimiento importado muestra su categoría. Pulsa Cambiar categoría, selecciona una opción y confirma con Guardar categoría. Cancelar descarta la selección. Las opciones iniciales son Ingresos, Alimentación, Suministros y Sin categoría.

Los tres conceptos del CSV de muestra tienen categorías iniciales definidas. Los demás conceptos aparecen Sin categoría para asignarlos manualmente. Los cambios se guardan por cuenta y movimiento en SQLite y se conservan al reiniciar y al reimportar el CSV. Para cargar esta versión, pulsa Intro en la ventana del lanzador y vuelve a abrir Ahorra+ desde la barra de tareas.

## Abrir con doble clic en Windows

Abre **Abrir Ahorra+.cmd** desde el Explorador de archivos. Usa las dependencias ya instaladas, elige puertos libres, configura la conexion entre la pagina y la API y abre el navegador. Conserva los movimientos guardados en demo-import.sqlite3.

Deja abierta la ventana de Ahorra+ mientras la usas. Para apagar los servicios que ha iniciado, vuelve a esa ventana y pulsa Intro. Para cargar cambios de codigo, apagala y abre de nuevo el mismo archivo. Cada arranque muestra la direccion correspondiente. Las terminales arrancadas manualmente se pueden detener con Ctrl+C.

Si faltan dependencias, el archivo indica que apartado seguir para instalarlas. Los registros de cada arranque se guardan en .local. Para comprobar solo las dependencias, ejecuta python iniciar.py --check desde esta carpeta.

## Importación CSV DEMO · Primer paso

La pantalla Inicio incluye selección de archivo, vista previa y confirmación en la versión web. Arranca la API y la app con EXPO_PUBLIC_API_URL según las instrucciones inferiores. Selecciona samples/movimientos-demo.csv. Comprueba las filas y pulsa Confirmar importación. Reimportar el mismo archivo muestra cero movimientos nuevos. Los errores de filas impiden confirmar.

La API protegida solo admite acceso desde el propio PC. En iPhone puedes probar la muestra integrada siguiendo el apartado inferior, sin importar ni guardar en la API. La versión nativa aún requiere un selector de archivos. La vista previa web en Windows acepta archivos de hasta 500 KB.

Desde esta carpeta, ejecuta `python -m api.csv_import samples/movimientos-demo.csv` para ver los movimientos ficticios. Repite añadiendo `--confirmar` para guardarlos en `demo-import.sqlite3`. Una segunda confirmación del mismo lote añade cero movimientos. Un ID existente con datos distintos bloquea el lote completo.

La importación usa las columnas fijas `id,fecha,concepto,importe`, fechas ISO e importes EUR con punto decimal. Cada ID identifica un movimiento dentro de su cuenta. Valida el archivo completo antes de escribir. El mapeo de columnas queda pendiente. Inicio carga la cuenta DEMO importada con saldo inicial 0 € y muestra sus movimientos hasta el corte del 14 de noviembre de 2026. Los cargos posteriores quedan guardados para su fecha. Tras confirmar, el resumen se actualiza automáticamente.

Primera pantalla de Inicio con una muestra ficticia. El corte del 14 de noviembre de 2026 muestra **3.248,40 €** de saldo, **942,30 €** de pagos comprometidos, **600,00 €** de ahorro protegido y **1.706,10 €** disponibles.

Con la API conectada, la cuenta importada se añade a las dos cuentas de la muestra. El CSV incluido aporta 2.006,85 € y tres movimientos. El saldo total pasa a 5.255,25 € y el disponible a 3.712,95 €. La vista integrada sin API conserva la muestra original.

## Windows · Abrir en el navegador

Abre PowerShell en esta carpeta. Necesitas Node.js LTS compatible con Expo SDK 54 (como Node 22) y acceso a npm para la instalación inicial.

```powershell
Set-Location app
npm.cmd ci
npm.cmd run web
```

Abre http://localhost:8081. Para comprobar el diseño estrecho, activa la vista móvil en las herramientas del navegador. Los datos DEMO incluidos permiten usar la pantalla sin iniciar Python.

## iPhone · Safari en la misma Wi-Fi

En PowerShell, desde `app`, genera la versión web y sírvela con Python 3.11 o posterior.

```powershell
npm.cmd run build
python -m http.server 8080 --bind 0.0.0.0 --directory dist
```

Usa `ipconfig` para identificar la IPv4 del Wi-Fi del PC. En Safari abre `http://IP_DEL_PC:8080` (por ejemplo, `http://192.168.1.25:8080`). Ambos equipos deben estar en la misma red privada. Si Windows pregunta, permite acceso para redes privadas únicamente. Detén el servidor con Ctrl+C al terminar.

Para probar la versión nativa, puedes usar Expo Go si la versión instalada en el iPhone es compatible con SDK 54. Ejecuta `npm.cmd start -- --lan` desde `app` y escanea el QR. Expo Go puede pedir iniciar sesión en Expo Go y en el CLI con la misma cuenta gratuita. Si aparece un aviso de incompatibilidad, usa Safari para probar sin coste. [Compatibilidad de Expo Go](https://docs.expo.dev/troubleshooting/expo-go-version-mismatch/) · [Inicio en dispositivo físico](https://docs.expo.dev/get-started/start-developing/).

## API local opcional

Desde la carpeta que contiene este README, en otra ventana de PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

La documentación interactiva está en http://127.0.0.1:8000/docs y el resumen en http://127.0.0.1:8000/api/v1/demo/home. Para activar el botón de actualización en la web del PC, vuelve a arrancar Expo con estas instrucciones desde `app`:

```powershell
$env:EXPO_PUBLIC_API_URL = 'http://127.0.0.1:8000'
npm.cmd run web
```

Si Expo usa otro puerto, configura `AHORRA_WEB_ORIGINS` con el origen exacto en la ventana de la API y reiníciala. Para la prueba en iPhone, genera el sitio desde una ventana sin `EXPO_PUBLIC_API_URL` para usar la muestra integrada.

## Verificación

Desde la raíz ejecuta `python -m unittest discover -s tests -v`. Comprueba importes, vencidos, cargos conciliados, corte de mes en año bisiesto, déficit y coincidencia entre la API de datos y la muestra de Expo. Desde `app`, ejecuta `npm.cmd run check` y `npm.cmd run build`.

Para regenerar la muestra desde la raíz en Windows, ejecuta `cmd.exe /c "python -m api.demo > app\demo.json"`.

Consulta [la especificación](ESPECIFICACION.md) para el plan completo y [los límites de seguridad](PRIVACIDAD.md) antes de acordar el próximo hito. Para incluir las pruebas de la API, ejecuta los tests con el Python que tenga instalado requirements.txt.



