# PetMatch

Plataforma web y API mobile-first para relacionar mascotas perdidas con observaciones de la comunidad. Esta primera entrega deja preparado el entorno local y el CRUD seguro de cuentas, mascotas, casos de pérdida, observaciones y metadatos de fotos. Las fases de análisis de IA y matching todavía no están implementadas.

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

Las rutas de escritura, las fotos y los datos privados de mascotas/casos requieren bearer token. Las observaciones son visibles públicamente sin datos de contacto y con coordenadas redondeadas; las coordenadas precisas se conservan en la base para uso interno futuro. Las fotos se guardan privadas en MinIO y se entregan con URL firmada de 15 minutos. Moderación, IA, vectorización, mapa y avisos quedan para las siguientes fases. PostGIS y pgvector se habilitan en PostgreSQL; el esquema de ubicación usa coordenadas numéricas en esta fase inicial.

## Pruebas de API

Con Python 3.12 o superior:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

Los tests usan SQLite temporal y no requieren Docker ni servicios externos.

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
  api/       FastAPI, SQLAlchemy, Alembic y tests
  web/       Next.js, TypeScript y Tailwind
infrastructure/docker/postgres/  PostGIS + pgvector
docker-compose.yml               PostgreSQL, Redis, MinIO, API y web
```

