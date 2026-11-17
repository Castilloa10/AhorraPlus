# Ahorra+ · Especificación de producto y técnica

Ahorra+ ayuda a saber cuánto dinero se puede usar sin comprometer pagos ni objetivos. El producto arranca en español, en euros y para una persona con varias cuentas propias. El coste de servicios es 0 € mediante ejecución local, SQLite y lógica propia. El entrenador y el chat comienzan con reglas y consultas locales, sin APIs de IA de pago.

## Inicio

- Saldo total de las cuentas incluidas, al cierre de la fecha de referencia.
- Pagos comprometidos pendientes hasta fin de mes, incluidos los vencidos. Cada gasto fijo o irregular tiene su propia fecha de cargo prevista. Cuando llega el movimiento, prevalece su fecha de cargo real y se concilia el pendiente.
- Ahorro protegido como dinero ya incluido en el saldo y reservado para objetivos. La cantidad objetivo y la reserva efectivamente financiada se guardarán por separado.
- Disponible = saldo total − pagos comprometidos − ahorro protegido. Un resultado negativo muestra el déficit. Los ingresos futuros entran en la proyección cuando se implemente, y el saldo de hoy se basa en cargos contabilizados.
- La DEMO usa un corte fijo del 14 de noviembre de 2026, una muestra ficticia y horizonte hasta el 30 de noviembre. Los pagos de diciembre quedan fuera del cálculo.

## Producto por hitos

1. Inicio DEMO con los cuatro importes, cuentas y pagos. API local y motor reproducible, almacenamiento SQLite en memoria para la muestra. Criterio de aceptación: UI estrecha y ancha y cifras conciliadas con la API.
2. Importación CSV con mapeo de columnas, previsualización, validación de fechas e importes, confirmación e historial de lotes. Usar ID externo si existe y señalar coincidencias dudosas para revisión. Reimportar un lote confirmado debe ser idempotente. Distinguir transferencias propias, devoluciones y gastos. Probar con archivos sintéticos.
3. Presupuestos mensuales por categoría, calendario de cargos, conciliación de gastos fijos e irregulares y reservas para objetivos con seguimiento. Usar la fecha real para imputar gastos al mes y conservar la fecha prevista como historial.
4. Análisis de comercios con nombres normalizados, recurrencias y cambios de frecuencia o importe. Proyección de saldo por día con supuestos, horizonte y escenarios. El entrenador avisa de déficits y patrones relevantes y ordena alternativas por viabilidad, impacto, coste y preferencias. Mostrar datos, supuestos y efecto de cada opción. Aplicar cambios internos solo tras aprobación explícita y registrar la decisión.
5. Chat financiero basado en consultas a los datos de Ahorra+. Citar movimientos, periodos y presupuestos que respaldan cada respuesta e indicar cuándo faltan datos. Las propuestas siguen el mismo flujo de aprobación del entrenador.
6. Diseñar un adaptador de conexión bancaria cuando se apruebe ese hito, con consentimiento revocable, sincronización idempotente y revisión del coste antes de elegir proveedor.

## Arquitectura

Expo y React Native Web comparten la pantalla para web, iOS y Android. FastAPI expone JSON versionado. El motor Python recibe datos tipados y calcula el resumen con enteros en céntimos. SQLite queda detrás de un repositorio. Para la DEMO, cada consulta carga la misma muestra en una base en memoria. La app abre con una captura del resumen generado por el motor y permite recargarlo si se configura la API local.

Entidades iniciales: cuenta propia, compromiso y reserva. Las siguientes serán movimiento contabilizado, lote de importación, categoría, presupuesto, objetivo y recomendación. El módulo de importación define la interfaz de lectura y el movimiento normalizado. La vista previa y la escritura transaccional entran en el siguiente hito.

La API de esta fase se limita a datos ficticios. Antes de incorporar datos personales se diseñarán almacenamiento persistente privado, autenticación para acceso remoto y controles de exportación y borrado.

## Hito de protección local implementado

En Windows, el repositorio abre SQLite en memoria y cifra su persistencia con DPAPI del usuario. Incluye conversión del archivo DEMO anterior, escrituras atómicas, bloqueo entre instancias de esta versión y pruebas de fallo, concurrencia y conservación de datos. Las claves y sesiones de prueba permanecen en el servidor dentro del almacén cifrado. La API restringe cliente, host y origen al uso local. Inicio incorpora desconexión local de prueba y borrado confirmado de importaciones, conservando presupuestos y pagos previstos. El acceso a la API desde iPhone y otros equipos queda deshabilitado en esta fase; la muestra integrada sigue disponible. La conexión real, revocación remota, recuperación portable y protección en otros sistemas siguen pendientes. Consulta PRIVACIDAD.md para activación y límites.

