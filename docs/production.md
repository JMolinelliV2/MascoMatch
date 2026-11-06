# Operación del servidor

Revisado el **5 de noviembre de 2026**. Esta guía corresponde al Compose de producción en Linux. Para instalar desde cero, utilizar [puesta en producción paso a paso](puesta-en-produccion-paso-a-paso.md). Para el entorno local, utilizar el [README del repositorio](../README.md).

## Alcance y configuración

Web, API, PostgreSQL, Redis, SeaweedFS, modelos, workers y respaldos se ejecutan en el VPS. La PC personal solo puede actuar como terminal administrativa. PostgreSQL, Redis, fotos y Ollama permanecen en redes privadas; Caddy publica HTTP/HTTPS y Prometheus se limita a loopback.

`.env.production` contiene opciones del despliegue y `.secrets/` los archivos privados. `production_init.py` crea una instalación sin sobrescribir claves; las opciones `--prepare-b2-secrets` y `--prepare-payment-secrets` preparan archivos faltantes en instalaciones existentes. Mantener `backup_key` también fuera del VPS, en una ubicación privada independiente.

Una integración escrita no prueba que esté activa: comprobar SMTP, DNS, modelos, proveedor de direcciones, pagos, B2 y receptor de alertas en ese entorno. No se transfieren la base local, sus datos ni su cuenta administradora al clonar el repositorio.

## Comandos comunes

Desde la raíz del checkout en el VPS, definir en esa terminal:

```sh
dc() {
  docker compose -p mascomatch --env-file .env.production -f compose.production.yml --profile ai-local --profile monitoring "$@"
}
```

La función se utiliza en los ejemplos siguientes. No combinar este archivo con `docker-compose.yml` de desarrollo ni mostrar la configuración completa en registros compartidos: usar `dc config --quiet` para validarla.

```sh
dc config --quiet
dc ps
python3 tools/production_apply.py check
docker stats --no-stream
df -h /
dc logs --tail 80 api worker worker-ai backup caddy
```

El chequeo comprueba dependencias, modelos habilitados, respaldo registrado y configuración SMTP. No confirma recepción de correo, eficacia de identidad ni una restauración real. La fecha de captura y la confirmación externa de B2 se revisan por separado en administración.

## Actualización y migraciones

1. Revisar `git status --short`, obtener las referencias con `git fetch origin` y revisar la versión que se va a desplegar. Integrar cualquier cambio local autorizado, como la regla HTTPS de `www`; no descartarlo automáticamente.
2. Cuando el checkout y la revisión estén aprobados, actualizar con `git pull --ff-only origin main` o seleccionar la revisión concreta revisada.
3. Ejecutar el despliegue durante una ventana de mantenimiento:

```sh
python3 tools/production_apply.py deploy --with-ai
python3 tools/production_apply.py check
```

El script construye las imágenes y detiene API/workers/backup antes de modificar el esquema. Prepara DB y fotos, crea un respaldo completo local previo en una instalación existente, ejecuta las migraciones y permisos, verifica/prepara modelos, recupera trabajos interrumpidos, programa faltantes y arranca los servicios. En una base nueva crea su copia inicial después de migrarla. El respaldo de seguridad del despliegue usa `--local-only`: no espera a B2 ni aplica poda.

La primera instalación de Gemma exige que el responsable lea y acepte sus términos antes de añadir `--accept-gemma-terms`. Sin esa opción se reutiliza una instalación cuyo manifiesto y hashes ya coincidan. No se descargan modelos durante solicitudes públicas.

La revisión de base se obtiene del propio checkout, sin depender de un número copiado de una entrega antigua:

```sh
dc run --rm --no-deps migrate alembic heads
dc exec -T api alembic current
```

La imagen y las migraciones deben pertenecer a la misma versión. No ejecutar un checkout antiguo contra un esquema nuevo como supuesto rollback. Para recuperar exactamente otra versión, conservar el entorno afectado y restaurar el respaldo compatible en destinos nuevos y vacíos.

Modificar variables o archivos de secretos requiere recrear el servicio correspondiente. Por ejemplo:

```sh
dc up -d --no-deps --force-recreate api
```

B2 requiere recrear `backup`; valores incorporados durante la construcción, como el país de búsqueda, requieren reconstruir/desplegar la web. Un simple `restart` no aplica variables nuevas.

## Correo y contacto

### Configuración

Los correos de cuenta, avistamientos, coincidencias, recordatorio de fotos y contacto utilizan el mismo transporte SMTP. [Flujos del sistema](FLUJOS_DEL_SISTEMA.md#16-notificaciones-y-correos) define sus disparadores; [mail_templates.py](../apps/api/app/mail_templates.py) centraliza HTML, texto alternativo y logo por CID.

Para Brevo, completar los valores no secretos en `.env.production`:

```dotenv
MAIL_DELIVERY_MODE=smtp
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_TLS_MODE=starttls
SMTP_USERNAME=LOGIN_SMTP
SMTP_FROM=MascoMatch <info@mascomatch.com>
PUBLIC_SITE_URL=https://mascomatch.com
```

Guardar únicamente la clave SMTP en `.secrets/smtp_password`, mediante un editor privado. No utilizar la API key como contraseña SMTP ni variables `NEXT_PUBLIC_` para secretos. Seguir los permisos de los archivos generados: directorio privado y archivos individuales legibles por los servicios a los que se montan. Recrear la API después de cambiar valores o claves.

Verificar dominio/remitente y cuota en el proveedor; conservar los registros de correo que ya funcionen al cambiar DNS web. Una clave en una instalación local no demuestra que exista en el VPS.

| Modo | Comportamiento |
| --- | --- |
| `smtp` | Envía mediante el proveedor configurado, con SSL o STARTTLS. |
| `preview` | Captura mensajes en Mailpit; se utiliza en desarrollo y es rechazado en producción. |
| `disabled` | No envía. Registro y nuevas solicitudes de enlaces de cuenta devuelven indisponibilidad. Contacto sigue recibiendo mensajes pendientes para administración. |

Los enlaces válidos ya emitidos conservan su vencimiento aunque se desactive el envío. Confirmación y cambio de correo vencen a las 24 horas; recuperación, a los 30 minutos. Abrir por GET el enlace de confirmación no lo consume: se confirma mediante la acción de la página. Las preferencias de alertas no desactivan correos de acceso solicitados por la persona.

### Alertas, reintentos y diagnóstico

Las solicitudes quedan en PostgreSQL antes de enviarse. La API procesa las colas en segundo plano; una alerta puede agruparse y se vuelve a comprobar elegibilidad, cuenta, correo confirmado, lectura, archivo, estado del aviso y preferencia antes del envío. Leer o archivar puede cancelar un correo todavía pendiente. No se reenvía automáticamente una alerta solo porque termine otra revisión de IA.

`SENT` significa que SMTP aceptó el mensaje; no confirma lectura ni bandeja de entrada. Un corte después de esa aceptación y antes de guardar el resultado puede producir un reintento duplicado. El identificador del mensaje se conserva, pero no se garantiza entrega exactamente una vez.

El panel muestra historial de intentos y solicitudes pendientes por separado. `PREVIEWED` no cuenta como envío real. Comprobar enlaces de producción, errores sanitizados y cuota antes de volver a solicitar mensajes repetidamente.

Para comprobar deliberadamente una entrega a la casilla del operador:

```sh
dc exec -T api python -m app.ops.release_check --send-test-email info@mascomatch.com
```

Ese comando sí envía un correo real. Abrirlo en la casilla y revisar spam; el chequeo ordinario sin esa opción no realiza ese envío.

### Contacto y recordatorios

Contacto guarda primero la solicitud, envía exclusivamente a `info@mascomatch.com` y utiliza el correo declarado en Reply-To sin considerarlo verificado. No hay acuse automático al visitante. Se aplican `RATE_LIMIT_CONTACT` y `RATE_LIMIT_CONTACT_DAILY`; el transporte desactivado no impide guardar la consulta.

Los fallos de contacto admiten hasta cinco intentos; agotados, quedan en `FAILED`. Tras corregir SMTP, el operador puede reprogramarlos:

```sh
dc exec -T api python -m app.contact_mail --retry-failed
```

Este comando habilita el reenvío posterior de mensajes pendientes; no utilizarlo como una consulta de solo lectura. Los enviados o previsualizados se eliminan de la base después de 30 días; pendientes/fallidos se conservan. Eso no elimina mensajes ya recibidos ni copias de respaldo.

El recordatorio de fotos se programa al crear un aviso de pérdida, con espera predeterminada `PHOTO_REMINDER_DELAY_MINUTES=30`. Solo envía si el aviso sigue activo, visible y sin fotos propias o heredadas, con dueño elegible y preferencia habilitada. No se programa para borradores ni reportes de encontrado. Recomienda varias imágenes y abre la gestión de fotos en Mis avisos.

## Administración

La cuenta debe estar activa, confirmada y asignada mediante `admin_access`. En una base nueva reservar la dirección desde el servidor:

```sh
dc exec -T api python -m app.admin --email info@mascomatch.com
```

El comando reserva la dirección si aún falta la cuenta o confirmación; no crea una contraseña ni permite el acceso por el mero nombre del correo. El procedimiento y las definiciones del panel están en [Administración](admin-operations.md).

## Respaldos y recuperación

### Copia local

El servicio `backup` realiza una copia al comenzar y repite cada `BACKUP_INTERVAL_SECONDS`, por defecto 21600 segundos. `BACKUP_LOCAL_KEEP=14` conserva catorce copias locales, aproximadamente 3,5 días al intervalo predeterminado.

Cada `.mbak` incluye una instantánea consistente de PostgreSQL, fotos y avatares referenciados y un manifiesto con hashes. Se cifra y autentica con AES-256-GCM y una clave independiente. Solo se registra éxito después de verificar el archivo. No basta con un volcado SQL si faltan las imágenes.

Para una copia manual, evitar que el daemon esté creando otra: esperar o detener `backup`, ejecutar el comando y volver a levantar el servicio al terminar:

```sh
dc stop backup
dc run --rm --no-deps backup python -m app.ops.backup create /backups --local-only
dc up -d --no-deps --force-recreate backup
```

La opción `--local-only` crea y verifica sin esperar a B2 ni podar. Un proceso ocupado devuelve 2; no retirar el bloqueo para forzar concurrencia. Revisar y corregir un fallo antes de dar la copia por válida. La comprobación de un archivo existente es:

```sh
dc exec -T backup python -m app.ops.backup verify /backups/ARCHIVO.mbak
```

El límite actual es 1 GiB de archivo descifrado, 20.000 fotos y 2 GiB de almacenamiento temporal en la configuración de recuperación. Ampliar y comprobar código/recursos antes de superarlo; no interpretar el tamaño del disco contratado como un aumento automático de ese límite.

### Copia externa y restauración

B2 está desactivado por defecto. La [guía B2](backblaze-backup.md) es la fuente única para bucket, Object Lock, lifecycle, credenciales, comprobaciones y recuperación desde otra máquina. Sus claves solo se entregan a `backup`; no se usan para servir fotos públicas.

Con B2 activo se conservan las copias locales sin confirmación remota aunque superen catorce. Vigilar el espacio durante fallos prolongados. La hora de subida no sustituye la fecha de captura recuperable.

La restauración es manual, con aplicación detenida, clave AES original y destinos vacíos. [backup.py](../apps/api/app/ops/backup.py) autentica el archivo antes de modificar datos y rechaza bases con tablas de aplicación o buckets con objetos. `restore` utiliza un archivo local; `restore-offsite` descarga una versión B2 y aplica el mismo control. Después se aplican permisos/migraciones compatibles y se comprueban usuarios, publicaciones y fotos antes de habilitar tráfico.

Conservar fuera del servidor la clave de recuperación, la configuración necesaria y referencias de versiones B2 verificadas. Los modelos/pesos y el código no son fotos de usuarios incluidas en el respaldo. Git protege el código, no la base ni los objetos privados. La copia solo en el mismo VPS no cubre su pérdida.

## Monitoreo

`/health/ready` comprueba DB, Redis y bucket. `/internal/ready/ai` agrega servicios de IA y requiere autorización privada; no realiza una inferencia. `/internal/metrics` requiere el token de monitoreo. Caddy no publica esos accesos internos.

Prometheus mantiene sus reglas en [alerts.yml](../infrastructure/production/alerts.yml). Observar disponibilidad, antigüedad de cola, fallos de correo, respaldos, captura remota, falta de señal, espacio y verificación profunda. Las cantidades y fechas no contienen textos, contactos ni imágenes.

El Compose **no configura un receptor de las reglas ni Alertmanager**. Brevo en la API no hace que Prometheus envíe automáticamente correos. Se necesita integrar ese receptor y un monitor fuera del VPS: una caída total también apaga el Prometheus del servidor. Los pasos de configuración y el túnel privado están en [la instalación](puesta-en-produccion-paso-a-paso.md#18-completar-monitoreo-y-envío-de-alertas).

## IA, validación y recuperación de fallos

[IA local](ai-production.md) define modelos, espacios compatibles, colas, backfill y evaluación. Los comandos operativos permiten cambiar de proveedor visual o pausar Gemma sin reinterpretar vectores:

```sh
python3 tools/production_apply.py fallback
python3 tools/production_apply.py pause-ai
python3 tools/production_apply.py resume-ai
```

`fallback` selecciona OpenCLIP si está habilitado; `pause-ai` desactiva Gemma manteniendo lo visual; `resume-ai` vuelve al perfil completo y programa faltantes. No sustituyen una restauración de base. El despliegue sin `--with-ai` respeta las banderas configuradas; añadirlo activa la IA.

`python3 tools/production_validate.py` prepara un stack desechable sin puertos públicos y con correo capturado en Mailpit. Las inferencias reales se comprueban aparte con `python3 tools/production_apply.py smoke`, en una ventana adecuada por su uso de recursos. El smoke técnico no mide precisión con identidades distintas ni volumen sostenible.

Ante errores, conservar los volúmenes y revisar el paso fallido. No usar borrados de volúmenes o una poda general como solución. Registrar fecha, revisión, estado y códigos sanitizados; no copiar secretos, cuerpos privados ni configuración completa a tickets o al repositorio.
