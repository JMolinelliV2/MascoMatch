<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/mascomatch-logo-dark.png">
    <img src=".github/assets/mascomatch-logo-light.png" alt="MascoMatch" width="360">
  </picture>
  <p><strong>Cada pista suma. Cada reencuentro importa.</strong><br>
  Tecnología y comunidad para ayudar a que más mascotas vuelvan a casa.</p>
  <p><img src=".github/assets/mascomatch-badges.png" alt="Perros y gatos · IA local · Publicar y buscar gratis" width="400"></p>
  <p>
    <a href="#levantar-en-local"><strong>Empezar</strong></a> ·
    <a href="docs/README.md">Documentación</a> ·
    <a href="docs/architecture.md">Arquitectura</a> ·
    <a href="https://github.com/JMolinelliV2/MascoMatch/issues">Ideas y problemas</a>
  </p>
</div>

---

MascoMatch conecta a quienes buscan a su perro o gato con las personas que lo vieron o lo tienen a salvo. Reúne avisos, fotos, mapas y posibles coincidencias para acompañar la búsqueda hasta el reencuentro.

## Qué ofrece

- **Avisos completos.** Código único, características y hasta cinco fotos con miniatura elegida.
- **Pistas desde la comunidad.** Direcciones, mapas ajustables y avistamientos breves desde una ficha, también sin cuenta.
- **Contacto con privacidad.** Quien tiene una mascota puede enviar sus fotos y datos desde el aviso; el dueño accede al contacto después de reconocerla.
- **IA local y revisión humana.** Comparación de fotos y características, con respuestas de los dueños para seguir la calidad de las recomendaciones.
- **Seguimiento y gestión.** Notificaciones web y correo, gestión de publicaciones y panel privado de administración y moderación.

## Cómo funciona

1. **Publicá su aviso:** contá cómo es y dónde se perdió; sumá fotos si las tenés.
2. **La comunidad aporta pistas:** alguien puede reportar que la vio o que la tiene a salvo.
3. **Revisá la evidencia:** consultá fotos, datos y posibles coincidencias desde tu cuenta.
4. **Confirmá el reencuentro:** cuando vuelva con vos, cerrá la búsqueda como recuperada.

Los reportes dirigidos a un aviso llegan al dueño aunque la IA siga pendiente. Reconocer a la mascota y recuperarla físicamente son acciones distintas. El [documento de flujos](docs/FLUJOS_DEL_SISTEMA.md) explica cada recorrido y sus permisos.

## Tecnologías

**Next.js · React · TypeScript · FastAPI · PostgreSQL · PostGIS · pgvector · Redis · Docker**

Gemma y Pet-ReID procesan evidencia en infraestructura propia, con RF-DETR y OpenCLIP según la configuración. Leaflet, OpenStreetMap y Photon resuelven mapas y direcciones. La [arquitectura](docs/architecture.md) explica el papel de cada tecnología.

## Levantar en local

Requisitos: Docker Desktop iniciado, Docker Compose v2 y los puertos locales disponibles: 3000, 8000, 5432, 6379, 9000 y 9001. Mailpit utiliza además el 8025 cuando se habilita su perfil.

Desde la carpeta del repositorio, en PowerShell:

```powershell
if (!(Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
docker compose up --build
```

El `.env` es privado. No reemplazar una configuración existente con el ejemplo. Las imágenes de PostgreSQL/PostGIS/pgvector y MinIO se construyen según los archivos de `infrastructure/docker`; la primera construcción puede tardar. La API local aplica las migraciones antes de iniciar. La web de desarrollo comprueba cambios de archivos para funcionar también en Windows/OneDrive.

Para crear cuentas hace falta un transporte de correo: configurar SMTP o el buzón local Mailpit descrito abajo.

<details>
<summary><strong>Servicios locales y cómo detener el proyecto</strong></summary>

| Servicio | Dirección local |
| --- | --- |
| Web | [localhost:3000](http://localhost:3000) |
| API y OpenAPI | [localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) |
| Estado de API | [localhost:8000/health](http://localhost:8000/health) |
| Consola MinIO | [localhost:9001](http://localhost:9001) |
| Mailpit, si está habilitado | [localhost:8025](http://localhost:8025) |

Para detener conservando los datos:

```powershell
docker compose down
```

No agregar `-v` si se quieren conservar base, fotos y modelos. Clonar o hacer push no copia esos datos.

</details>

## Configuración y desarrollo

<details>
<summary><strong>Correo de prueba con Mailpit</strong></summary>

El registro necesita un transporte de correo activo. Para probar sin enviar mensajes externos, editar el `.env` privado:

```dotenv
MAIL_DELIVERY_MODE=preview
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_TLS_MODE=none
SMTP_USERNAME=
SMTP_PASSWORD=
PUBLIC_SITE_URL=http://localhost:3000
```

Aplicar y abrir el buzón local:

```powershell
docker compose --profile mail-local up -d --build
```

Los enlaces de confirmación y recuperación se consultan en Mailpit. `preview` no envía a la casilla real. Para correo real, usar `smtp` y configurar el proveedor según [operación](docs/production.md#correo-y-contacto). `restart` no aplica cambios de variables; recrear con `up -d`.

</details>

<details>
<summary><strong>Instalar y habilitar la IA local</strong></summary>

La publicación no espera una inferencia. Con la IA habilitada, Gemma extrae características y Pet-ReID representa las fotos de perros/gatos, con detector local y OpenCLIP como alternativa explícita. PostgreSQL conserva los trabajos; Redis/RQ los entrega a los workers.

La [guía de IA](docs/ai-production.md#instalación-en-desarrollo-local) contiene instalación de pesos fijados, configuración, backfill y evaluación. No basta con activar una variable: deben estar instalados los modelos y levantados los workers. El operador acepta los términos de Gemma antes de su primera instalación. No se necesita una API paga de IA.

</details>

<details>
<summary><strong>Ejecutar las comprobaciones de desarrollo</strong></summary>

API, con Python 3.12 y desde `apps/api`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
$env:APP_ENV="test"
$env:MAIL_DELIVERY_MODE="disabled"
$env:AI_ENABLED="false"
$env:EMBEDDINGS_ENABLED="false"
python -m pytest -q -p no:cacheprovider
```

La suite ordinaria utiliza bases temporales y proveedores simulados. Las integraciones reales se activan por separado, en entornos desechables. No usar las cuentas o publicaciones reales como fixtures.

Web, con Node.js 22 y desde `apps/web`:

```powershell
npm ci
npm test
npm run typecheck
npm run build
```

GitHub Actions ejecuta comprobaciones de API/web, migraciones PostgreSQL, reglas de monitoreo y dependencias. Un resultado antiguo de pruebas no acredita el estado de una revisión nueva.

[Ver el estado de las verificaciones en GitHub Actions](https://github.com/JMolinelliV2/MascoMatch/actions/workflows/ci.yml).

</details>

<details>
<summary><strong>Desplegar en producción</strong></summary>

[El procedimiento de instalación](docs/puesta-en-produccion-paso-a-paso.md) usa `compose.production.yml` en un VPS Linux, separado del Compose local. Web, API, base, fotos, cola y modelos corren allí; no dependen de que la PC personal esté encendida. Se generan secretos propios y no se copian credenciales de desarrollo.

SMTP, DNS, búsqueda de direcciones, [B2](docs/backblaze-backup.md), [Mercado Pago](docs/mercado-pago-configuracion.md) y el receptor de alertas se configuran y comprueban por instalación. El repositorio no demuestra que esas cuentas externas ya estén operativas.

</details>

<details>
<summary><strong>Estructura del repositorio</strong></summary>

```text
apps/api/                   API, workers, modelos de datos, migraciones y tests
apps/web/                   Páginas, componentes, mapas y proxies de sesión
infrastructure/docker/      Imágenes de servicios de datos
infrastructure/production/  HTTPS, permisos y monitoreo
tools/                      Inicialización, despliegue y validación aislada
test-data/                  Fixtures y formatos de evaluación
docs/                       Guías vigentes
```

</details>

## Guías del proyecto

- [Flujos implementados](docs/FLUJOS_DEL_SISTEMA.md): publicación, cuentas, avistamientos, contacto y recuperación.
- [Arquitectura](docs/architecture.md): tecnologías, datos y procesamiento.
- [Puesta en producción](docs/puesta-en-produccion-paso-a-paso.md): instalación inicial en un VPS.
- [Operación](docs/production.md): correo, actualizaciones, monitoreo y respaldos.

El [índice de documentación](docs/README.md) reúne las guías de IA, administración, métricas, B2 y Mercado Pago.

## Participar y apoyar

Para sugerir mejoras o informar un problema, [abrí un issue](https://github.com/JMolinelliV2/MascoMatch/issues) con el recorrido y lo que ocurrió. Las pull requests deben explicar el propósito y las comprobaciones realizadas.

Publicar y buscar es gratuito. Los aportes voluntarios ayudan a sostener infraestructura, correo, respaldos y procesamiento de IA. La integración de aportes puntuales en UYU está documentada en la [guía de Mercado Pago](docs/mercado-pago-configuracion.md).
