# Avistamientos desde un aviso y alertas al dueño

> Documento de una etapa anterior. Ver el [estado actual del MVP](mvp-phase-3-8.md), que incorpora comparación visual local, matching general, mapa y paneles.

Entrega del 7 de octubre de 2026.

## Función disponible

Desde una ficha de **Animales perdidos**, **Publicar un avistamiento** abre `/avistamiento?aviso=<case_id>`. El formulario muestra el animal seleccionado y pide:

- Ubicación, por búsqueda, GPS o ajuste del pin.
- Hasta 4 fotos opcionales, JPEG/PNG/WebP de hasta 10 MB cada una.
- Hora actual con **Lo vi recién**, o fecha y hora aproximadas al desmarcarlo.

Se puede enviar sin crear una cuenta. La referencia al aviso se conserva en `Observation.linked_case_id`. La descripción generada indica que la identidad está por confirmar; las características del aviso son contexto y no se copian como evidencia independiente del avistamiento.

## Comparación y alertas

El servicio `app/matching/linked.py` compara este avistamiento con el aviso seleccionado:

1. El aviso debe estar activo y el avistamiento ser posterior a la pérdida, con hasta un minuto de tolerancia del reloj.
2. La ubicación debe estar dentro de `search_radius_meters` del aviso, más hasta 1 km de tolerancia GPS de cada punto.
3. Sin foto, genera un **avistamiento por confirmar**. Las fotos inconclusas o un análisis fallido también permiten revisión humana con esa etiqueta.
4. Con resultados visuales disponibles, compara especie, color, tamaño, pelaje, patrón y tipo/raza. Usa atributos de confianza mínima 0,7, al menos 0,5 de peso compatible y puntuación normalizada de 0,75 por defecto.
5. Una especie o color claramente diferente, una fecha incompatible o una ubicación fuera del radio impiden generar la alerta. Las fotografías compatibles se presentan como **posible coincidencia**, nunca como identificación segura.

Pesos: especie 0,35; color 0,30; tamaño, longitud del pelaje y patrón 0,10 cada uno; tipo/raza 0,05. La puntuación es una regla de compatibilidad y no una probabilidad de identidad. Se utilizan resultados vigentes del proveedor/modelo/versión actuales. Las declaraciones del dueño tienen prioridad como descripción del animal buscado.

Cada avistamiento tiene como máximo una notificación. La persona autenticada que creó el aviso no recibe una alerta de su propio reporte. Las peticiones repetidas conservan el mismo UUID y hash de datos para evitar duplicaciones; reutilizar el UUID con datos diferentes devuelve 409.

Los cambios de aviso, mascota o fotos vuelven a poner la comparación en pendiente e invalidan las alertas previas mientras se revisa. Un reconciliador recupera pendientes cada 5 segundos. El worker ejecuta la comparación al terminar el análisis de IA; la detección funciona sin que el dueño visite la página.

## Bandeja privada

**Notificaciones** permite entrar con la cuenta del aviso, ver el lugar en un mapa, las fotos y los motivos de compatibilidad, y marcar alertas como leídas. El indicador de navegación actualiza la cantidad sin leer. El enlace del correo abre la alerta correspondiente y requiere la cuenta del dueño.

La sesión usa una cookie `HttpOnly`, `SameSite=Lax`, con `Secure` en producción. Los cambios desde la web comprueban el origen. La web consulta la API interna usando esa cookie; la clave SMTP se utiliza exclusivamente en el backend. Una sesión vencida no impide enviar un avistamiento como visitante.

Las fotos permanecen en el bucket privado y la ruta de cada alerta verifica el dueño del aviso, el avistamiento y la foto. La ubicación precisa del avistamiento se comparte solo en la alerta privada. El correo contiene fecha y localidad, sin coordenadas precisas ni fotos adjuntas. Los avistamientos públicos mantienen coordenadas aproximadas.

## Correo y Brevo Free

El envío SMTP tiene una cola persistente en la notificación, hasta 5 intentos con espera creciente, preferencia por usuario y cancelación de avisos inactivos. Usa TLS con certificados verificados en el modo real. Un envío aceptado por SMTP queda como `SENT`; esto no acredita recepción, lectura ni ausencia de filtrado como spam.

**Brevo Free** permite 300 correos diarios y no requiere tarjeta. Su documentación indica que el excedente de correo transaccional puede quedar en cola. La cuenta, la autenticación del dominio y el remitente deben configurarse en Brevo antes de activar el servicio. [Plan gratuito](https://help.brevo.com/hc/es/articles/208589409-Informaci%C3%B3n-sobre-los-planes-de-precios-de-Brevo), [límites](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan), [SMTP](https://help.brevo.com/hc/en-us/articles/7924908994450-Send-transactional-emails-using-Brevo-SMTP).

En `.env`, para un remitente propio ya verificado:

```dotenv
MAIL_DELIVERY_MODE=smtp
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=TU_LOGIN_SMTP_DE_BREVO
SMTP_PASSWORD=TU_CLAVE_SMTP_DE_BREVO
SMTP_FROM=MascoMatch <avisos@tu-dominio.example>
SMTP_TLS_MODE=starttls
PUBLIC_SITE_URL=https://tu-sitio.example
```

Usar una **clave SMTP**, no una clave de API de IA. Guardarla solo en `.env`, que sigue excluido de Git. La cuenta gratuita se puede abrir desde la web de Brevo; no se creó una cuenta externa ni se configuraron credenciales en esta entrega.

```powershell
docker compose --profile ai-local up -d api worker web
```

La instalación actual mantiene `MAIL_DELIVERY_MODE=disabled` hasta completar la configuración. Las alertas quedan guardadas en la bandeja y los correos pendientes. La API y el worker tienen que permanecer encendidos; un despliegue público requiere una URL accesible para abrir los lugares y fotos desde otros dispositivos.

### Pruebas locales de correo

Se agregó Mailpit, con panel en `http://localhost:8025`, limitado a la interfaz local y SMTP disponible solo entre contenedores. El modo `preview` captura correos y los marca `PREVIEWED`; no equivale a enviar correos a destinatarios reales. [Mailpit](https://mailpit.axllent.org/docs/install/docker/).

```powershell
docker compose --profile mail-local up -d mailpit
```

La prueba de integración configura el modo local únicamente para su base de datos aislada. No modifica las alertas reales ni las preferencias de los usuarios.

## Archivos y variables

- Backend: `app/routers/linked_sightings.py`, `notifications.py`, `app/matching/linked.py`, `app/notifications/email.py`, modelos, esquemas y dependencias.
- Hooks: análisis completado, edición de avisos/mascotas/avistamientos y cambios de fotos. Limpieza de alertas al eliminar un aviso o avistamiento.
- Migración: `0005_linked_sightings`, columnas del avistamiento y nueva tabla de notificaciones; conserva los registros existentes.
- Frontend: `linked-sighting-form.tsx`, navegación desde la ficha, bandeja, indicador, mapa de solo lectura y rutas de sesión/avistamientos/notificaciones.
- Configuración: `docker-compose.yml`, `.env.example`. `WATCHFILES_FORCE_POLLING=true` corrige la recarga de la API desde el volumen de Windows/OneDrive. [Watchfiles](https://watchfiles.helpmanual.io/api/watch/).
- Nuevas variables: `LINKED_MATCH_THRESHOLD`, `LINKED_FEATURE_CONFIDENCE`, `API_INTERNAL_URL`, `MAIL_DELIVERY_MODE`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TLS_MODE`, `PUBLIC_SITE_URL`.

## Comprobaciones

- API: **104 pruebas aprobadas y 2 integraciones optativas omitidas** en la ejecución normal.
- Frontend: **22 pruebas aprobadas**; TypeScript sin errores y compilación correcta.
- PostgreSQL real en `0005_linked_sightings (head)`; servicios en ejecución.
- Recorrido HTTP por la web con una cuenta temporal: cookie `HttpOnly`, avistamiento anónimo, recuperación de sesión vencida, bandeja privada, enlace del correo, marcado como leído y rechazo de otro origen. Los registros temporales se eliminaron conservando los avisos existentes.
- Navegador: el botón dentro del aviso de Pepe abre su formulario vinculado sin solicitar datos del animal ni cuenta.

- Pruebas regulares de API: casos sin foto, imagen compatible, contradicciones, fotos inconclusas, fallos de análisis, fotos múltiples, deduplicación, permisos, lecturas, edición, cierre, limpieza y preferencias/reintentos SMTP.
- Migración nueva con una base vacía y con registros existentes, más downgrade/upgrade.
- Frontend: mensajes de incertidumbre, formatos de hora, sesión, origen y límite de carga; TypeScript y compilación.
- Integración real aislada: Redis/RQ, Ollama `gemma3:4b`, MinIO y SMTP de Mailpit. Dos fotos analizadas, notificación privada, dos correos capturados y comprobación de que no se duplican los envíos. **1 prueba aprobada en 67,51 s**, con dos avisos de deprecación de `fork` emitidos por RQ/Python 3.12.

Ejecutar la integración:

```powershell
docker compose cp ./apps/web/public/images/dog-hero.jpg api:/tmp/linked-check-dog.jpg
docker compose exec -T -e RUN_LINKED_INTEGRATION=1 -e AI_SMOKE_IMAGE_PATH=/tmp/linked-check-dog.jpg api python -m pytest tests/test_linked_integration.py -q -s -p no:cacheprovider
```

## Pendientes y límites

- Activar el correo externo con la cuenta, el dominio/remitente y la clave SMTP. La entrega externa no está comprobada mientras falten esos datos.
- Esta comparación cubre avistamientos vinculados por una persona a un aviso específico. Embeddings, ranking entre todos los avisos, push y moderación de producción quedan para las fases siguientes.
- Los umbrales son heurísticos y la prueba con la foto de ejemplo comprueba el recorrido técnico; no mide precisión de identificación. La duración depende del equipo y la cola. Las cuotas, los filtros de correo y el estado del servidor impiden garantizar entrega instantánea.
