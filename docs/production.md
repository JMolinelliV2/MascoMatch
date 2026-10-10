# Preparación para producción

Entrega del 9 de octubre de 2026. Este archivo describe un despliegue Docker en un servidor Linux. No publica automáticamente el dominio ni contrata servicios.

## Cambios

- Imágenes de API y web con usuario sin privilegios, código dentro de la imagen y dependencias fijadas. La web usa el servidor de producción de Next.js.
- Caddy termina HTTPS y administra sus certificados. Solo publica 80 y 443; PostgreSQL, Redis, fotos, Ollama y workers tienen redes privadas. La web y Caddy se separan de la red de datos.
- PostgreSQL tiene un propietario para migraciones y un usuario de aplicación sin privilegios de superusuario ni creación de tablas o roles.
- Los secretos se montan en los servicios que los necesitan. El worker de visión no recibe claves de firma de sesiones ni SMTP y tiene credenciales de fotos de lectura.
- Sesiones con identificador almacenado, expiración y revocación. Salir invalida el token en el servidor. La web conserva el token únicamente en una cookie HttpOnly, Secure y con prefijo `__Host-` en producción.
- Las sesiones anteriores a esta entrega necesitan un nuevo ingreso una sola vez. Las cuentas, contraseñas y avisos se conservan.
- Contraseñas nuevas de al menos 12 caracteres; PBKDF2 SHA-256 con 600.000 iteraciones. Los hashes anteriores se actualizan al ingresar, manteniendo las contraseñas existentes.
- Confirmación de correo y recuperación mediante enlaces de un solo uso. Los códigos se guardan como hash y cifrados para su envío; vencen a las 24 horas y 30 minutos respectivamente. Restablecer la contraseña revoca las sesiones. En producción, el correo de alertas espera a que el dueño confirme su dirección.
- Límites compartidos en Redis por cuenta o dirección verificada del cliente. Un proxy ajeno no puede suplantar esa dirección. Si Redis falla, el acceso y las escrituras se suspenden temporalmente; las lecturas conservan límites locales.
- Las cargas de fotos tienen un máximo de tres solicitudes simultáneas en la web, con permisos temporales que vencen. Caddy limita el tamaño del cuerpo y su tiempo de lectura. Las escrituras de la API pasan por los proxies de la web.
- Registros de solicitudes con identificador, ruta general, duración y estado; se omiten cuerpos, consultas, direcciones y contactos. Los errores SQL no imprimen parámetros.
- Respaldos cifrados diarios, conservación de catorce copias y verificación de integridad antes de restaurar. Recuperar exige destinos vacíos.
- Métricas privadas y reglas de Prometheus para disponibilidad, demora de análisis, fallos de correo y respaldos atrasados. Integración continua para pruebas, compilación y auditoría de dependencias de Python y web.

Los controles siguen las referencias de [sesiones de OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [contraseñas de OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [secretos de Compose](https://docs.docker.com/compose/how-tos/use-secrets/) y [contadores atómicos de Redis](https://redis.io/docs/latest/commands/incr/).

## Fotos

La instalación local conserva MinIO. Su [repositorio está archivado](https://github.com/minio/minio); el despliegue nuevo usa SeaweedFS 4.48 y su [API S3](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-S3-API). Las claves de la aplicación acceden a `pet-photos`; la inicialización usa una clave administrativa separada. El bucket es privado y conserva versiones de los objetos.

Las fotos se recuperan desde el respaldo manteniendo sus claves y las relaciones en PostgreSQL. No hay que reemplazar ni borrar el volumen local para preparar el servidor.

## Preparar el servidor

En la carpeta del proyecto, con Python 3 y Docker Compose instalados:

```sh
python3 tools/production_init.py --domain mascomatch.com
docker compose -p mascomatch --env-file .env.production -f compose.production.yml up -d --build
```

El generador crea `.env.production` y `.secrets/` y **rechaza sobrescribir claves existentes**. Ambos están excluidos de Git. La carpeta privada tiene permisos 0700 en Linux; los archivos se entregan como montajes individuales de lectura a los contenedores, sin montar la carpeta completa. Guardar `backup_key` en otra ubicación privada antes de depender de los respaldos.

El archivo de producción es independiente: no combinarlo con `docker-compose.yml`, que contiene puertos y montajes de desarrollo. DNS debe apuntar al servidor para que Caddy obtenga el certificado. El servidor debe permitir 80/TCP, 443/TCP y, si se usa HTTP/3, 443/UDP. Prometheus publica únicamente 9090 en loopback para acceso mediante SSH.

El punto de partida no activa IA ni SMTP. Esto permite instalar los modelos y configurar Brevo antes de habilitarlos. Para IA local, reservar memoria adicional: la configuración limita Ollama a 6 GB y el worker visual a 2 GB, además de los otros servicios. Dimensionar el servidor con mediciones de uso; esos límites no son una prueba de capacidad ni una garantía de latencia.

Para instalar los modelos en el servidor:

```sh
docker compose -p mascomatch --env-file .env.production -f compose.production.yml --profile ai-local build worker
docker compose -p mascomatch --env-file .env.production -f compose.production.yml --profile ai-local up -d ollama
docker compose -p mascomatch --env-file .env.production -f compose.production.yml exec ollama ollama pull gemma3:4b
docker compose -p mascomatch --env-file .env.production -f compose.production.yml --profile ai-local run --rm --no-deps --user 0 -v mascomatch_vision_models:/models/clip:rw worker python -m app.embeddings.setup
```

El último comando utiliza permisos de instalación solo en ese contenedor temporal. El worker habitual sigue sin privilegios y con los modelos en lectura. El nombre del volumen corresponde al proyecto `-p mascomatch`; ajustarlo si se cambia ese nombre. Después activar `AI_ENABLED` y `EMBEDDINGS_ENABLED` en `.env.production`:

```sh
docker compose -p mascomatch --env-file .env.production -f compose.production.yml --profile ai-local up -d api worker
docker compose -p mascomatch --env-file .env.production -f compose.production.yml --profile ai-local run --rm --no-deps worker python -m app.embeddings.setup
```

La segunda ejecución registra las fotos existentes para procesamiento con el modelo ya instalado. El funcionamiento está detallado en [la entrega del MVP](mvp-phase-3-8.md).

## Brevo

Para la instalación local, los valores se configuran en `.env` como antes. Para el servidor:

- Completar `SMTP_USERNAME`, `SMTP_FROM`, `SMTP_HOST`, `SMTP_PORT` y `SMTP_TLS_MODE` en `.env.production`.
- Guardar la clave SMTP en `.secrets/smtp_password`, sin incluirla en el repositorio ni pasarla como argumento de comandos.
- Mantener privada la carpeta y permitir la lectura del archivo montado a los contenedores. Recrear la API para aplicar valores o archivos nuevos.
- Cambiar `MAIL_DELIVERY_MODE` a `smtp` cuando el dominio y el remitente estén verificados en Brevo.
- Registrar/ingresar una cuenta, confirmar su correo y comprobar recepción con un avistamiento de prueba.

Los mensajes de confirmación, recuperación y avistamientos utilizan el mismo SMTP. Las preferencias de alertas no desactivan un correo solicitado para recuperar la cuenta. Solicitar recuperación devuelve la misma respuesta exista o no el usuario. Cada cuenta tiene un máximo de tres enlaces nuevos por hora y una separación mínima de un minuto.

El correo de recuperación incluye una versión HTML con el logo y los colores de MascoMatch, un botón para elegir una contraseña y el enlace completo como alternativa. El logo viaja incorporado en el mensaje mediante CID, sin depender de una URL pública de imágenes. Se mantiene una versión de texto para lectores que no muestran HTML. Ambas versiones indican el vencimiento de 30 minutos y el uso único del enlace.

Cuando `MAIL_DELIVERY_MODE=disabled`, solicitar recuperación o un nuevo correo de confirmación devuelve HTTP 503: no se anuncia un envío que no puede ocurrir. Los enlaces ya emitidos siguen pudiendo consumirse hasta su vencimiento. El modo `preview`, exclusivo del desarrollo, indica en el formulario que el enlace está en Mailpit y no en la casilla real.

### Recuperación en desarrollo local

Configurar estas variables en `.env` (archivo privado excluido de Git):

```dotenv
MAIL_DELIVERY_MODE=preview
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_TLS_MODE=none
PUBLIC_SITE_URL=http://localhost:3000
```

Aplicar la configuración a la API y levantar el buzón local:

```powershell
docker compose --profile mail-local up -d --no-deps mailpit api
```

Solicitar el enlace en `http://localhost:3000/recuperar` y abrir el correo en `http://localhost:8025`. El envío se procesa cada diez segundos. El enlace de recuperación vence a los treinta minutos y sirve una sola vez. Mailpit captura los correos localmente; para recibirlos en una casilla real hay que configurar SMTP con el servicio externo. Esta configuración local no se utiliza en producción.

```sh
docker compose -p mascomatch --env-file .env.production -f compose.production.yml up -d --force-recreate api
```

En la instalación local, aplicar cambios de `.env` con `docker compose --profile ai-local up -d api worker`; `restart` solo vuelve a iniciar contenedores con sus variables anteriores.

## Respaldos y recuperación

El servicio `backup` arranca con una copia y repite cada 86.400 segundos. Captura una instantánea PostgreSQL con `pg_dump`, guarda las fotos referidas por esa misma instantánea y un manifiesto con hashes. El archivo final usa AES-256-GCM y una clave distinta de las credenciales de la aplicación. Si falta una foto o falla una comprobación, no se publica una copia incompleta. Las versiones retenidas permiten leer una foto eliminada durante la captura.

```sh
docker compose -p mascomatch --env-file .env.production -f compose.production.yml exec backup python -m app.ops.backup create /backups
docker compose -p mascomatch --env-file .env.production -f compose.production.yml exec backup python -m app.ops.backup verify /backups/ARCHIVO.mbak
```

Esta primera configuración limita el archivo descifrado a 1 GB, hasta 20.000 fotos y usa almacenamiento temporal de 2 GB para recuperar. Antes de superar esa capacidad hay que ampliar y probar el almacenamiento temporal y el presupuesto de respaldo. La retención conserva las últimas catorce copias; comprobar espacio disponible y exportar copias cifradas a otra ubicación. Un respaldo en el mismo servidor no cubre la pérdida de ese servidor.

Para recuperar, preparar un entorno aislado con una base PostgreSQL sin tablas de aplicación y un bucket vacío, con la aplicación detenida. Entregar la clave original de respaldo al servicio de recuperación y la URL del destino en un archivo privado. Ejecutar:

```sh
python -m app.ops.backup restore /backups/ARCHIVO.mbak --target-database-file /run/secrets/restore_database_url
```

El comando verifica autenticidad, rutas y hashes antes de modificar destinos. Rechaza una base con tablas de aplicación o un bucket con objetos. Luego ejecutar la aplicación de permisos de `app.ops.database` con el propietario de la base y poner en marcha API, web y workers. Mantener intacta la instalación anterior hasta comprobar usuarios, avisos, fotos y acceso en la recuperada.

## Monitoreo

```sh
docker compose -p mascomatch --env-file .env.production -f compose.production.yml --profile monitoring up -d prometheus
```

`/internal/metrics` exige el token de monitoreo y no se publica mediante Caddy. `/health/ready` verifica PostgreSQL, Redis y acceso autenticado al bucket. Las métricas contienen cantidades y tiempos, sin contactos ni fotos. Prometheus muestra alertas; queda por configurar un destino de avisos operativos para el operador cuando se elija el servidor. La entrega de un correo no garantiza que el proveedor lo haya colocado en la bandeja de entrada.

## Evaluar coincidencias

Copiar `test-data/matching/real-dataset.example.json` a una carpeta `real-data/` privada, agregar fotografías distintas y etiquetas de identidad conocidas. Incluir animales parecidos que no sean el mismo, positivos, negativos y reportes sin foto. Separar consultas de calibración y de evaluación final; el evaluador rechaza imágenes repetidas entre referencias y consultas, o entre ambos grupos.

```sh
python -m app.matching.real_evaluate real-data/labels.json --output real-data/metrics.json
```

Se ejecuta con el worker y el modelo CLIP instalado, montando esa carpeta solo para lectura. Produce métricas agregadas de ranking y alertas, sin fotos ni contactos. Las características se proporcionan en el dataset; no mide por sí solo la calidad del extractor de texto/fotos. Si no se informan distancias y fechas, el reporte marca que se usó un contexto controlado. **Todavía no hay un conjunto real suficiente ni precisión de identificación medida.** No ajustar umbrales mirando las imágenes de evaluación final.

## Comprobaciones de esta entrega

- API: 163 pruebas aprobadas y cuatro integraciones opcionales omitidas en la ejecución habitual, con bases temporales.
- Web: 24 pruebas aprobadas, tipos comprobados y compilación del servidor de producción completada.
- Dependencias: `pip-audit` no encontró vulnerabilidades conocidas en la imagen final de API ni en la del worker después de actualizar los paquetes observados. En el worker, las versiones CPU de Torch y Torchvision se consultaron con su versión upstream para cubrir las mismas fuentes. Dependencias de producción web: `npm audit` informó cero vulnerabilidades. La integración continua repite estas auditorías.
- Entorno de producción aislado: registro por la web sin devolver el token al navegador, cookie protegida, publicación con foto, rechazo de origen ajeno y cierre con revocación.
- Restauración real: recuperación de PostgreSQL y fotos desde un archivo cifrado; hashes coincidentes y rechazo de un destino que ya contenía tablas.
- Redis: contadores atómicos verificados con solicitudes concurrentes y admisión limitada a tres cargas simultáneas.
- Monitoreo: configuración y cinco reglas válidas; lectura autenticada de métricas por Prometheus, rechazo sin token y comprobación de dependencias disponible.
- Worker nuevo: PyTorch 2.13.0 CPU y Torchvision 0.28.0; modelo CLIP existente cargado con UID 10001 y representación de 512 números normalizada a partir de una imagen sintética. La pareja de versiones sigue la [distribución oficial de PyTorch](https://pytorch.org/get-started/previous-versions/).
- La instalación local conserva sus dos avisos, una foto y un embedding. No se realizó envío de correo externo, configuración de DNS ni publicación del dominio.

Estas comprobaciones validan el recorrido técnico. No miden precisión de identificación con mascotas reales ni capacidad bajo tráfico de producción.

## Antes de publicar

- Elegir el servidor y configurar DNS/HTTPS.
- Completar Brevo y probar confirmación de correo, recuperación y alertas en cuentas controladas.
- Recuperar una copia en otro entorno y exportar respaldos fuera del servidor, con la clave guardada por separado.
- Configurar el destino de los avisos operativos y medir capacidad, espacio y demora con el uso previsto.
- Reunir el conjunto de fotografías etiquetadas y calibrar el ranking antes de interpretar una puntuación como buena identificación.

Esta entrega prepara los mecanismos y su configuración. La disponibilidad pública, las pruebas de correo real y las mediciones de uso requieren el servidor y el SMTP configurados.
