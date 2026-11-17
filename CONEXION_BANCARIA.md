# Conexión bancaria de Ahorra+

## Revisión pública del 15 de noviembre de 2026

Conclusión: Enable Banking es una opción viable sobre el papel para uso personal con cuentas propias y coste del servicio de 0 €, sujeta a sus condiciones. No se ha registrado una aplicación, aceptado contratos, conectado cuentas ni verificado una cuenta concreta.

- Cobertura: el listado oficial, consultado en el navegador y filtrado por Openbank, muestra Openbank / Open Bank, S.A. / Spain, con AISP y PISP y entornos Sandbox y Production. Ahorra+ solo contemplaría información de cuentas, saldos y movimientos. No se implementarán pagos. La cobertura anunciada no garantiza cada producto, historial ni disponibilidad de una cuenta concreta. Fuente: https://enablebanking.com/open-banking-apis
- Coste: las condiciones actualizadas el 9 de enero de 2026 permiten uso personal gratuito restringido a cuentas propias vinculadas. Pueden existir límites de cuentas y consultas. El uso comercial o profesional exige otro acuerdo; la gratuidad no se puede extrapolar a una futura app para terceros. Fuente: https://enablebanking.com/terms/
- Alta futura: activar una aplicación de producción vinculando cuentas y autorizar el acceso de la propia aplicación son pasos distintos. No se ha realizado ninguno. Fuente: https://enablebanking.com/docs/api/linked-accounts/
- Privacidad: según el aviso del proveedor de 7 de marzo de 2025, los datos bancarios pasan por sus servidores y se retienen para conversión hasta 60 segundos; los datos de sesión pueden conservarse hasta 180 días y los datos de IP/navegador 30 días. Declara tratamiento en el EEE con proveedores de nube. La política también contempla credenciales de inicio de autorización cuando un banco las requiere; no se ha comprobado el flujo concreto de Openbank. No afirmar que la información nunca sale del PC. Fuente: https://tilisy.enablebanking.com/privacy
- Revocación: el portal Data Sharing Consents permite autenticarse, consultar servicios autorizados y terminar su acceso. La API permite eliminar una sesión y solo promete cerrar el consentimiento del banco cuando sea posible. Borrar los datos locales es una operación diferente. Fuentes: https://enablebanking.com/data-sharing-consents/ y https://enablebanking.com/docs/api/reference/#delete-session

Antes de usar datos reales siguen pendientes: comprobar el flujo específico de autorización de Openbank, sus límites de historial y consultas, implementar y probar retorno seguro, caducidad, revocación remota y conciliación. Propuesta para acordar con el usuario: preparar primero un flujo de consentimiento y desconexión con datos ficticios; cualquier registro externo y autorización bancaria se decidirán por separado.

## Estado actual

La pantalla incluye una simulación local con un archivo sintético. Convierte dos movimientos contabilizados a nuestro formato de importación, muestra una vista previa y solicita confirmación. El destino es la cuenta DEMO importada. El efecto total es −20 €. Repetir la confirmación conserva los movimientos existentes. El movimiento pendiente queda excluido.

El adaptador usa la fecha de contabilización, la referencia estable y el sentido débito o crédito. Comprueba moneda, precisión e información necesaria. Una página con continuación se rechaza hasta implementar la descarga completa. La documentación distingue entry_reference como identificador estable y transaction_id como identificador que puede cambiar. [Referencia de Enable Banking](https://enablebanking.com/docs/api/reference/)

## Decisiones para revisar juntos antes de usar datos reales

- Confirmar cobertura de Openbank España para la cuenta concreta, límites de uso y coste vigente.
- Revisar los términos de Enable Banking y el tratamiento de datos como intermediario.
- Acordar cuentas, historial solicitado, duración del acceso y frecuencia de actualización.
- Preparar protección del almacenamiento local y de la clave privada del proveedor, acceso a la API y registros sin información sensible.
- Revisar una pantalla de consentimiento para lectura de cuentas, saldos y movimientos, con revocación y borrado local.
- Validar identidad de cuentas, paginación, reintentos, cambios de identificadores, movimientos pendientes y conciliación de saldos antes de activar sincronización.

Esta versión incorpora almacenamiento local cifrado con DPAPI, restricciones de acceso local y controles de borrado y desconexión local de prueba. Hay que reiniciar las APIs antiguas para activar la conversión. Consulta [protecciones y límites](PRIVACIDAD.md). Estas medidas no habilitan ni certifican una conexión bancaria real.

## Flujo previsto para autorizar

Registrar la aplicación con el proveedor, consultar los bancos disponibles, solicitar acceso, abrir la autorización oficial y verificar el retorno. Después se obtiene la sesión para consultar los datos autorizados. La clave privada se mantiene en el servidor local. La sesión necesita controles de expiración y revocación. [Documentación de autorización](https://enablebanking.com/docs/api/reference/)

El acceso personal restringido exige vincular cuentas propias y completar también la autorización de la aplicación. Sus condiciones deben revisarse antes de activarlo. [Vinculación de cuentas propias](https://enablebanking.com/docs/api/linked-accounts) · [Condiciones](https://enablebanking.com/terms/)
