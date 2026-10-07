# PetMatch

Plataforma web y API mobile-first para relacionar mascotas perdidas con observaciones de la comunidad. Incluye el CRUD de cuentas, mascotas, casos, observaciones y fotos, y la fase de extracción de características de textos y fotos con IA local. Los embeddings, las coincidencias, las alertas y el mapa son las siguientes fases.

## Requisitos

- Docker Desktop con Docker Compose v2.
- Puertos locales disponibles: 3000, 5432, 6379, 8000, 9000 y 9001.

## Levantar el proyecto

En PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

La primera construcción instala PostGIS y pgvector sobre la imagen oficial `postgres:17-bookworm`, compila MinIO desde su código fuente e instala las dependencias de la aplicación. Puede tardar unos minutos. MinIO usa la versión fija `RELEASE.2025-10-15T17-29-55Z`, sin depender de la imagen retirada de Docker Hub. La API aplica la migración inicial antes de arrancar.

- Web: http://localhost:3000
- API y OpenAPI: http://localhost:8000/api/v1/docs
- Health check: http://localhost:8000/health
- MinIO console: http://localhost:9001
- Redis: localhost:6379
- PostgreSQL: localhost:5432

Para bajar los servicios, conservando datos:

```powershell
docker compose down
```

Para borrar también los volúmenes locales (elimina los datos):

```powershell
docker compose down -v
```

## API inicial

Rutas bajo `/api/v1`:

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET|POST /pets`, `GET|PATCH|DELETE /pets/{id}`
- `GET|POST /lost-cases`, `GET|PATCH|DELETE /lost-cases/{id}`
- `GET|POST /observations`, `GET|PATCH|DELETE /observations/{id}`
- `POST /photos/upload` (valida, limpia EXIF, reduce y almacena una imagen privada; máximo 10 MB)
- `GET|POST /photos`, `GET /photos/{id}/url`, `PATCH|DELETE /photos/{id}`

Las rutas de escritura, las fotos, los análisis y los datos privados de mascotas/casos requieren bearer token. Las observaciones son visibles públicamente sin datos de contacto y con coordenadas redondeadas; las coordenadas precisas se conservan en la base para uso interno futuro. Las fotos se guardan privadas en MinIO y se entregan con URL firmada de 15 minutos. Moderación, vectorización, matching, mapa y avisos quedan para las siguientes fases. PostGIS y pgvector están habilitados en PostgreSQL.

## IA local: fase 2

El MVP usa **Ollama**, sin API keys ni proveedores pagos. El servicio incluido tiene `OLLAMA_NO_CLOUD=1` y no publica su puerto en el equipo. La configuración de la API rechaza proveedores distintos de Ollama, nombres de modelos cloud, servidores públicos y URLs con credenciales. El cliente de inferencia no utiliza proxies del sistema ni sigue redirecciones.

El modelo por defecto es `gemma3:4b`, compatible con texto e imágenes. La primera descarga ocupa varios GB y requiere conexión a Internet; la inferencia se realiza en el entorno local. La velocidad y la memoria necesaria dependen del equipo. El perfil usa CPU por defecto; no requiere configurar una GPU.

Desde la carpeta del proyecto:

```powershell
docker compose --profile ai-local up -d ollama
docker compose --profile ai-local exec ollama ollama pull gemma3:4b
```

Después agregá o cambiá esta línea en tu `.env`:

```dotenv
AI_ENABLED=true
```

Reconstruí e iniciá el proyecto y el worker. La API aplica la migración `0002_ai_extraction` al arrancar:

```powershell
docker compose --profile ai-local up --build -d
docker compose logs -f api worker
```

Con `AI_ENABLED=false`, los formularios y el CRUD siguen funcionando sin Redis para inferencia ni un modelo disponible. No se generan análisis nuevos. Los reportes creados antes de habilitar IA pueden analizarse con el endpoint POST indicado abajo.

### Funcionamiento

1. Crear o editar un caso o una observación guarda un trabajo de texto dentro de la misma transacción de base de datos. Cambiar características de una mascota actualiza el análisis de sus casos. Crear una mascota con campos ya estructurados no hace una consulta redundante al modelo.
2. Subir una foto guarda un trabajo de imagen. La request no llama al modelo.
3. Un despachador de la API entrega trabajos pendientes a Redis/RQ. Si Redis falla, el trabajo queda en la base y se retoma después.
4. El worker consulta Ollama, valida el JSON y guarda un `FeatureSet` privado con valor, confianza y origen de cada atributo.
5. Al guardar un reporte, la web consulta el estado y muestra características sugeridas separadas por descripción y foto. La descripción original y los datos declarados se conservan.

Los prompts están versionados. Datos faltantes o ambiguos usan `unknown`, `not_visible` o `uncertain`, con confianza cero. La confianza es una valoración no calibrada del atributo, no una probabilidad de identificar una mascota. El análisis no confirma coincidencias ni genera alertas en esta fase.

La inferencia recibe miniaturas de hasta 1024 píxeles, sin EXIF, y campos físicos. No se agregan nombres, contactos, microchips ni coordenadas a los inputs de IA. Si una persona escribe esos datos dentro de la descripción, forman parte de su texto original; el prompt indica ignorarlos para extraer características físicas. Los resultados y trabajos solamente son accesibles por el dueño del reporte.

Se deduplican trabajos por propietario, evidencia, modelo y versión de prompt. Hay hasta tres intentos por defecto, con espera entre fallos transitorios. Un modelo inexistente falla sin reintentos automáticos. Las ejecuciones interrumpidas se recuperan mediante leases; versiones antiguas de un trabajo no pueden sobrescribir una ejecución nueva. Las descripciones modificadas invalidan resultados anteriores y las eliminaciones borran los análisis relacionados. Los jobs usan serialización JSON, y sus logs incluyen IDs, estado, modelo y latencia, sin cuerpos de texto o imágenes.

### API de análisis

Siempre con `Authorization: Bearer <token>`:

| Método | Ruta | Uso |
| --- | --- | --- |
| GET | `/api/v1/analysis/{owner_type}/{owner_id}` | Estado y características vigentes |
| POST | `/api/v1/analysis/{owner_type}/{owner_id}` | Analizar evidencia existente; reutiliza trabajos ya creados |
| GET | `/api/v1/analysis/jobs/{job_id}` | Consultar un trabajo propio |
| POST | `/api/v1/analysis/jobs/{job_id}/retry` | Reintentar un fallo tras una espera mínima de 60 segundos |

`owner_type`: `pet`, `lost_case` u `observation`. Estados: `PENDING`, `DISPATCHING`, `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `STALE`. Las respuestas omiten snapshots de entrada y solo incluyen características vigentes. No incluyen embeddings.

### Variables de IA

| Variable | Valor por defecto en Compose | Función |
| --- | --- | --- |
| `AI_ENABLED` | `false` | Activa generación y despacho de análisis |
| `AI_TEXT_MODEL` | `gemma3:4b` | Modelo local para descripciones |
| `AI_VISION_MODEL` | `gemma3:4b` | Modelo local para fotos |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Servidor local en la red de Docker |
| `REDIS_URL` | `redis://redis:6379/0` | Cola de trabajos |
| `AI_REQUEST_TIMEOUT_SECONDS` | `180` | Límite por consulta, entre 10 y 600 segundos |
| `AI_MAX_ATTEMPTS` | `3` | Máximo de intentos automáticos, entre 1 y 5 |
| `AI_DISPATCH_INTERVAL_SECONDS` | `5` | Intervalo del despachador |

Para ejecutar la API o el worker fuera de Docker, usar `OLLAMA_BASE_URL=http://localhost:11434` y `REDIS_URL=redis://localhost:6379/0`, con Ollama en modo local. Un equipo lento puede requerir aumentar el timeout. Los cambios de variables requieren recrear los servicios con `docker compose --profile ai-local up -d`.

Referencias: [API de Ollama](https://docs.ollama.com/api/chat), [salidas estructuradas](https://ollama.com/blog/structured-outputs), [modo local](https://docs.ollama.com/faq), [modelo](https://ollama.com/library/gemma3:4b), [RQ](https://python-rq.org/docs/).

### Certificados de antivirus o proxy

Si la descarga falla con `x509: certificate signed by unknown authority` y Windows valida la conexión mediante el certificado de un antivirus o proxy, se puede incorporar esa autoridad pública al contenedor. Exportá únicamente el certificado de la autoridad que tu equipo ya confía, en formato PEM, a un archivo `.crt`:

```powershell
docker compose exec ollama mkdir -p /root/.ollama/certificates
docker compose cp ./mi-certificado.crt ollama:/root/.ollama/certificates/network-ca.crt
docker compose restart ollama
```

El directorio se conserva en el volumen de modelos. `SSL_CERT_DIR` agrega esos certificados al directorio del sistema dentro de Ollama; se mantiene la validación HTTPS. Los certificados del equipo no se incluyen en el repositorio. [Configuración de certificados de Go](https://pkg.go.dev/crypto/x509#SystemCertPool).

## Pruebas de API

Con Python 3.12 o superior:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

Los tests usan SQLite temporal y no requieren Docker ni servicios externos. La fase de extracción tiene pruebas de esquema, permisos, idempotencia, actualización de evidencia, reintentos, recuperación de workers, fallos de Redis, contratos HTTP de Ollama y migraciones desde una base nueva y desde el esquema inicial. Los proveedores de IA y la cola se simulan en estas pruebas; esto no mide la calidad real del modelo ni sustituye una prueba de Docker/PostgreSQL.

La prueba opcional de integración ejecuta un worker RQ real y consulta el modelo local. Usa una base SQLite separada y una cola con nombre único, que elimina al terminar; no modifica los reportes existentes. Requiere el perfil `ai-local`, el modelo descargado y la nueva imagen de API:

```powershell
docker compose exec -e RUN_LOCAL_AI_TESTS=1 -e AI_ENABLED=true api python -m pytest tests/test_local_ai_integration.py -q
```

Para incluir la fotografía de ejemplo de la portada:

```powershell
docker compose cp ./apps/web/public/images/dog-hero.jpg api:/tmp/petmatch-check-dog.jpg
docker compose exec -e RUN_LOCAL_AI_TESTS=1 -e AI_ENABLED=true -e AI_SMOKE_IMAGE_PATH=/tmp/petmatch-check-dog.jpg api python -m pytest tests/test_local_ai_integration.py -q
```

Estas comprobaciones validan el recorrido y dos ejemplos de extracción; no son una evaluación de precisión del matching.

## Variables de entorno

Copiar `.env.example` a `.env` antes de ejecutar Compose. Cambiar contraseñas y `JWT_SECRET` para entornos compartidos. La configuración real de producción, TLS, almacenamiento S3 administrado y secretos queda fuera de esta entrega.

## Ubicación en los formularios

La portada presenta una fotografía y tres acciones: mascota perdida, avistamiento y animal encontrado. Los formularios se completan en tres etapas: **Mascota**, **Fecha y lugar**, y **Contacto y revisión**. Se valida cada etapa al continuar; el botón Atrás conserva los datos y la foto seleccionada. La última etapa muestra un resumen editable antes de crear la cuenta o ingresar y guardar el reporte. Las fotos son opcionales.

El lugar se elige buscando una dirección, barrio o punto de referencia, o con el GPS del dispositivo. Los resultados deben seleccionarse para guardar su ubicación; escribir un texto sin elegir un resultado no asigna coordenadas. El GPS se solicita únicamente al tocar el botón y conserva la precisión que informa el dispositivo. Funciona en `localhost` o con HTTPS y requiere permiso del navegador.

La búsqueda usa Photon con datos de OpenStreetMap. `GEOCODER_BASE_URL` permite cambiar el servidor compatible; por defecto se usa `https://photon.komoot.io`, un servicio público de demostración que necesita conexión a Internet y no ofrece disponibilidad garantizada. Para un despliegue público con tráfico, configurar una instancia propia o un proveedor con capacidad contratada. Las direcciones se consultan desde la web a través de `/api/places`; las publicaciones conservan las coordenadas internas y solo agregan la localidad al texto, sin insertar automáticamente la dirección exacta.

Las sugerencias se restringen al país de la persona, determinado con una consulta inversa de la ubicación del dispositivo. Si no hay permiso o no se puede obtener esa referencia, se usa `NEXT_PUBLIC_SEARCH_COUNTRY` (por defecto `UY`, Uruguay), sin presentar ese valor como una ubicación detectada. El botón **Priorizar cerca de mí** solicita el permiso para ordenar las sugerencias sin seleccionar automáticamente el lugar del reporte. Si el navegador ya tiene permiso, se obtiene esa referencia al abrir el formulario. La ubicación elegida para el reporte y la referencia de la persona son independientes.

La consulta al proveedor usa `countrycode` y sesgo geográfico; el servidor vuelve a filtrar por país y ordena coincidencias exactas antes que coincidencias parciales, y dentro de cada grupo por distancia cuando existe una referencia del dispositivo. Los términos genéricos como “plaza” priorizan la cercanía. Se combina una búsqueda cercana con otra dentro del mismo país para recuperar coincidencias exactas lejanas. Nunca se amplía automáticamente la búsqueda a otros países si no hay resultados.

Validar frontend desde `apps/web`: `npm test`, `npm run typecheck` y `npm run build`.

## Estructura

```text
apps/
  api/       FastAPI, SQLAlchemy, Alembic, análisis local y tests
  web/       Next.js, TypeScript y Tailwind
infrastructure/docker/postgres/  PostGIS + pgvector
docker-compose.yml               PostgreSQL, Redis, MinIO, API, web y perfil ai-local (Ollama/RQ)
```

