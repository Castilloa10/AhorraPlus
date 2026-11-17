# Protección local · Hito DEMO

Esta versión sigue usando exclusivamente datos ficticios. No conecta bancos ni demuestra que la futura conexión bancaria esté preparada para datos reales.

## Activar la versión

1. Cierra Ahorra+ pulsando Intro en la ventana del lanzador. Detén también cualquier API antigua arrancada manualmente, con Ctrl+C en su terminal.
2. Abre Ahorra+ desde el acceso de la barra de tareas o desde Abrir Ahorra+.cmd.
3. Al leer por primera vez la base de datos anterior, esta versión comprueba su integridad y la convierte a formato cifrado. Conserva movimientos, categorías, presupuestos y cargos previstos.
4. Al final de Inicio aparece Privacidad · DEMO local. El borrado exige escribir BORRAR DEMO. No lo pulses para comprobar la instalación si quieres conservar tus pruebas.

No uses a la vez una API antigua y esta versión sobre el mismo archivo. Una versión antigua no podrá abrir el nuevo formato. No borres el archivo para intentar solucionar un error de lectura.

## Qué protege

SQLite se abre en memoria y se guarda cifrado con DPAPI, vinculado al usuario de Windows, sin contraseña propia ni servicio externo. El archivo sigue llamándose demo-import.sqlite3, pero ya no puede abrirse directamente con un visor SQLite. Las escrituras reemplazan el archivo de forma atómica y un bloqueo coordina las instancias de esta versión. Si falla el cifrado, no se guarda una copia en claro.

El módulo privado de claves y sesiones usa el mismo almacenamiento cifrado. No hay claves reales configuradas ni un formulario que las solicite. Ningún endpoint entrega esos secretos al navegador.

La API acepta clientes locales, verifica el nombre de servidor y restringe los orígenes del navegador; las operaciones de cambio requieren el origen autorizado. El lanzador configura ese origen. Las respuestas de la API indican que no deben almacenarse en caché. Esto no autentica otros programas que se ejecuten en el equipo y puedan enviar sus propias cabeceras.

## Controles de privacidad

- Desconectar autorización local de prueba elimina las claves y sesiones locales guardadas. No revoca permisos bancarios externos: esa integración no existe todavía.
- Borrar datos importados de prueba elimina movimientos, categorías manuales e historial de importación de la cuenta DEMO. Conserva presupuestos y pagos previstos. Permite volver a importar los archivos de muestra.

## Límites

Un programa malicioso ejecutándose como tu usuario podría descifrar estos datos o leer la memoria. DPAPI no sustituye la protección del equipo. La aplicación muestra datos al navegador y cualquier herramienta autorizada para observar esa pantalla podría verlos.

Copiar el archivo cifrado a otro ordenador o usuario no garantiza poder recuperarlo. No cambies de perfil, reinstales Windows ni borres su configuración esperando recuperar este archivo sin un plan de copia y recuperación probado. El prototipo no incluye aún exportación cifrada portable.

La conversión y el borrado lógico no garantizan borrar copias antiguas, archivos CSV originales, copias de seguridad, registros anteriores o restos recuperables del disco. No se han utilizado datos reales para las pruebas.

El servidor protegido funciona por ahora en Windows y solo desde el propio PC. Web, iOS y Android conservan la estructura compartida; para iPhone usa la muestra integrada, sin acceso a esta API. El acceso por red y la protección del almacenamiento en otros sistemas requieren otro hito acordado.

Antes de conectar Openbank faltan la revisión del proveedor y su coste, consentimiento, retorno de autorización seguro, caducidad y revocación remota, identidad de cuentas y pruebas completas de sincronización. Este hito no es una auditoría independiente de seguridad.

Referencias: [protección DPAPI de Microsoft](https://learn.microsoft.com/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata), [SQLite en Python](https://docs.python.org/3/library/sqlite3.html).
