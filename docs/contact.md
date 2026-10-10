# Contacto y sugerencias

`/contacto` permite sugerir mejoras, informar un problema o hacer una consulta sin iniciar sesión. Se accede desde Explorar, el menú móvil y el pie del inicio. Pide nombre, correo, tipo y mensaje de 10 a 4000 caracteres. Los campos se conservan ante un error y se muestra una confirmación después de guardar la solicitud.

## Correo

Los mensajes se envían exclusivamente a **info@mascomatch.com**, usando el SMTP y el remitente configurados para MascoMatch. No hay que agregar otra clave. El correo incluye nombre, dirección, tipo, mensaje, logo y una referencia. `Reply-To` permite responder directamente a la persona; su dirección es declarada, sin verificar. No se envía una respuesta automática al correo indicado.

La confirmación de la página indica que se recibió el mensaje, no que SMTP ya lo entregó en la bandeja. El envío se procesa cada diez segundos. Una solicitud repetida con el mismo identificador y contenido reutiliza el registro; un fallo de red permite reintentar sin crear otro correo pendiente.

Con `MAIL_DELIVERY_MODE=smtp`, el envío usa Brevo u otro SMTP real ya configurado. `preview` envía al buzón local Mailpit. `disabled` rechaza solicitudes con una explicación y ofrece la dirección de contacto.

## Entrega y operación

La migración `0017_contact_messages` agrega la cola privada en PostgreSQL. Los reinicios conservan solicitudes pendientes. Cada intento bloquea su registro; el envío admite hasta cinco intentos, con esperas crecientes. Tras agotarlos, queda en `FAILED` y se registra solo un identificador y la cantidad de intentos, sin mensajes ni contactos.

Las métricas privadas `mascomatch_contact_email_pending` y `mascomatch_contact_email_failed` informan los estados. La regla existente de fallos de correo también incluye contacto. Luego de corregir SMTP, se pueden volver a poner los mensajes fallidos en la cola:

```powershell
cd "C:\Users\jmoli\OneDrive\Escritorio\buscadorMascotas"
docker compose exec api python -m app.contact_mail --retry-failed
```

En producción, usar la misma operación con `-p mascomatch --env-file .env.production -f compose.production.yml`. El comando no imprime direcciones ni contenido.

Como en otros envíos SMTP, si el servidor acepta el correo y se interrumpe la conexión o el guardado de su resultado, un reintento podría repetirlo. El `Message-ID` y la referencia se mantienen. No se garantiza entrega exactamente una vez ni ubicación en la bandeja de entrada.

## Privacidad y límites

- Los mensajes no tienen un endpoint público de lectura y no se publican en la página. Solo se guardan en la base privada y se envían al buzón del proyecto.
- Los registros enviados o previsualizados se eliminan de la base después de 30 días; los pendientes y fallidos se conservan para entrega o revisión. Esto no borra el correo recibido ni copias de respaldo existentes.
- El servidor controla destinatario, asunto y remitente. Valida el correo, rechaza caracteres de control y escapa el contenido HTML.
- La web exige el origen permitido y limita el cuerpo a 24 KiB. La API limita el cuerpo también, no refleja datos en errores y rechaza campos adicionales.
- Un campo invisible ayuda a detectar automatizaciones simples. No sustituye un CAPTCHA ni garantiza ausencia de spam.
- `RATE_LIMIT_CONTACT=5` limita intentos por dirección cliente por hora. `RATE_LIMIT_CONTACT_DAILY=50` limita el total del formulario por día para preservar la capacidad de alertas. Son ventanas desde el primer intento y cuentan también intentos inválidos o repetidos.
- En producción los límites usan Redis y el proxy de confianza existente. Si falla Redis, el envío se rechaza temporalmente. En desarrollo, sin IP del visitante transmitida por un proxy de confianza, quienes usan la web local comparten el límite por dirección del servidor web.

## Revisión de esta entrega

Se comprobó TypeScript y la sintaxis Python. La API inició con `0017_contact_messages` aplicada, SMTP habilitado y cero solicitudes de contacto. La página respondió correctamente y la revisión visual mostró la tarjeta centrada con los cuatro campos, la acción de envío y la dirección alternativa, sin desbordamiento horizontal en escritorio. No se ejecutaron pruebas automatizadas ni se enviaron mensajes de contacto de prueba a una casilla real.
