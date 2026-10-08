# Fase 2: extracción de características con IA local

> Documento de una etapa anterior. Ver el [estado actual del MVP](mvp-phase-3-8.md), que incorpora comparación visual local, matching general, mapa y paneles.

Entrega del 7 de octubre de 2026.

## Implementación

- Extracción de texto y fotos mediante Ollama y `gemma3:4b`, sin API keys de proveedores pagos.
- Contratos separados `LLMProvider` y `VisionProvider`, y una fábrica reemplazable.
- Salida compacta del modelo, validada con Pydantic y convertida a atributos con valor, confianza y origen.
- Prompts versionados; datos desconocidos o ambiguos se conservan como tales, con confianza cero.
- Modelos `AnalysisJob` y `FeatureSet`, y migración `0002_ai_extraction`.
- Trabajos persistidos en la transacción del reporte, despacho periódico a Redis/RQ y worker separado.
- Deduplicación por evidencia/modelo/prompt, reintentos limitados con espera y recuperación de ejecuciones interrumpidas.
- Resultados privados y vigentes; actualizar o eliminar evidencia invalida o borra sus análisis.
- La pantalla de confirmación del reporte consulta el estado y muestra características sugeridas de texto y foto por separado.

## Archivos

| Área | Archivos |
| --- | --- |
| Extracción | `apps/api/app/analysis/schemas.py`, `prompts.py`, `providers.py` |
| Procesamiento | `apps/api/app/analysis/service.py`, `queue.py`, `tasks.py`, `worker.py`, `logging.py` |
| API y permisos | `apps/api/app/routers/analysis.py`, `services/access.py`, cambios en los routers CRUD y en `main.py` |
| Persistencia | `apps/api/app/models.py`, `migrations/versions/0002_ai_extraction.py` |
| Migración inicial | `0001_initial_core.py` ahora crea únicamente las cinco tablas de la fase inicial, evitando crear tablas futuras antes de su migración |
| Fotos y configuración | `apps/api/app/core/image_storage.py`, `core/config.py`, `requirements.txt` |
| Web | `apps/web/app/report-analysis.tsx`, `report-form.tsx`, `globals.css` |
| Infraestructura | `docker-compose.yml`, `.env.example` |
| Pruebas | `apps/api/tests/test_analysis.py`, `test_analysis_migrations.py`, `test_local_ai_integration.py`, actualización de `conftest.py` |
| Documentación | `README.md`, este documento |

## Decisiones

Se eligió Gemma 3 de 4B tras comparar ejemplos de extracción con otro modelo local. Extrajo el perro de color chocolate como marrón, el tamaño mediano y la marca blanca en el pecho; el ejemplo de gato sin collar ni manchas no produjo esos rasgos positivos. También procesó la fotografía de un perro. Esto valida estos ejemplos, no la precisión general del modelo.

Se mantienen las características originales del usuario y los resultados del modelo separados. No se considera la confianza informada una probabilidad de identidad. Las fotos se reducen a 1024 píxeles y se limpian antes de la inferencia.

El perfil de Docker tiene cloud deshabilitado y Ollama sin un puerto publicado en el equipo. La API rechaza proveedores externos, modelos cloud y endpoints públicos, y el cliente no utiliza proxies del sistema ni sigue redirecciones.

La conexión al registro de modelos estaba interceptada por Kaspersky. Se validó la cadena con Windows y se incorporó su certificado público al entorno de Ollama, manteniendo HTTPS. El certificado del equipo queda fuera de Git y se conserva en el volumen local. El modelo alternativo descargado para comparar fue retirado; queda `gemma3:4b` de 3.3 GB.

## Ejecutar

En este equipo ya está descargado el modelo y `.env` tiene `AI_ENABLED=true` y ambos modelos configurados como `gemma3:4b`.

```powershell
docker compose --profile ai-local up --build -d
docker compose logs -f api worker
```

La web está en `http://localhost:3000` y la API en `http://localhost:8000/api/v1/docs`.

Para un clon nuevo, seguir la sección de IA local del README: descargar el modelo, activar `AI_ENABLED` e iniciar el perfil. `.env` permanece excluido de Git.

## Pruebas

| Comprobación | Resultado |
| --- | --- |
| Pytest de API en Windows | 50 pruebas pasaron; la integración opcional se omite en la ejecución habitual |
| Pytest de API en Docker | 50 pruebas pasaron; integración opcional ejecutada por separado |
| Prueba real de integración | Pasó: dos textos (incluyendo negaciones) y una foto; Redis/RQ, procesos de worker nuevos, MinIO y Ollama reales |
| Frontend | 9 pruebas pasaron |
| TypeScript | `npm run typecheck` pasó |
| PostgreSQL | Migración aplicada, `alembic current`: `0002_ai_extraction (head)` |

La integración utiliza una base SQLite aislada, una cola con nombre único y un objeto de foto creado para la prueba; elimina su cola y foto al terminar. No modifica los reportes existentes. RQ/Python 3.12 emitió avisos de deprecación sobre `fork` al iniciar procesos durante la prueba; las ejecuciones se completaron correctamente.

Comandos y límites de las pruebas están documentados en el README. No se midieron Precision@K, Recall@K ni tasa de falsos positivos, porque el motor de matching todavía no está implementado.

## Variables nuevas

`AI_ENABLED`, `AI_TEXT_MODEL`, `AI_VISION_MODEL`, `OLLAMA_BASE_URL`, `REDIS_URL`, `AI_REQUEST_TIMEOUT_SECONDS`, `AI_MAX_ATTEMPTS`, `AI_DISPATCH_INTERVAL_SECONDS`. El proveedor del perfil es Ollama; el servicio define `OLLAMA_NO_CLOUD=1` y `SSL_CERT_DIR` para certificados locales opcionales. La tabla de defaults está en el README.

## Pendiente

Las fases siguientes son embeddings visuales locales y pgvector, recuperación y ranking de candidatos, alertas, mapa, feedback y moderación. Esta fase analiza evidencia; todavía no identifica posibles coincidencias ni envía notificaciones.
