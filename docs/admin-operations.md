# Panel privado: operación y moderación

Revisado el **5 de noviembre de 2026**. Esta guía reúne acceso, operación, moderación y seguimiento de recomendaciones. El [contrato de métricas](analytics.md) define las visitas, exposiciones y atribuciones de impacto.

## Acceso exclusivo

`/admin` exige sesión vigente, cuenta activa, correo confirmado, rol administrativo y la asignación única de `admin_access`. Todas las rutas administrativas lo comprueban. La tabla admite una sola asignación (`id = 1`); un rol aislado o conocer la URL no otorgan acceso.

La asignación se administra desde el servidor con `python -m app.admin`. Puede reservar una dirección antes de que exista o esté confirmada la cuenta. La confirmación válida vincula el UUID de esa cuenta; un cambio posterior de correo conserva su identidad. Eliminarla elimina la asignación y no reasigna el panel automáticamente. En otra base debe reservarse de nuevo, salvo que se haya recuperado su asignación mediante un respaldo compatible. Ver [comando de producción](production.md#administración).

El menú ofrece Administración solo cuando `/auth/me` devuelve `admin_access: true`. Las respuestas privadas usan `no-store`; los proxies web controlan sesión, rutas permitidas y origen de escrituras. Ningún permiso depende de ocultar botones.

## Funciones

| Sección | Información y controles |
| --- | --- |
| Resumen | Cuentas registradas, actividad por período y últimos 15 minutos, bloqueos, trabajos, correos y contactos. |
| Usuarios | Nombre, contacto, confirmación de correo, registro, última actividad y publicaciones actuales. Bloquear y reactivar con motivo y confirmación. |
| Trabajos | Espera, ejecución, completados, fallidos y reemplazados; modelo, intentos, fechas y código de error. |
| Correos | Un registro por intento real de envío; vistas previas separadas. Cola de solicitudes pendientes y fallidas. |
| Contactos | Nombre y correo declarados, mensaje recibido y estado de reenvío a administración. |
| Publicaciones | Avisos perdidos, avistamientos y encontrados, ID público, autor y estado. Ocultar y restaurar con motivo. |
| Auditoría | Acción, fecha, referencia del objetivo y motivo registrado. |
| Analytics | Visitas, recorridos, matching, impacto e inventario contextual; exportación agregada donde se ofrece. |
| Aportes | Operaciones puntuales de Mercado Pago, separadas entre pruebas y producción; consulta sin movimientos financieros. |
| Respaldos | Estado local/B2 informado por el servicio; no ejecuta restauraciones desde el panel. |
| Seguimiento de coincidencias | Recomendaciones únicas y respuestas de los dueños, con filtro de fecha y hora. |
| Denuncias y correcciones | Denuncias con período, estado y paginación; se conservan las correcciones de descripción y moderación de reseñas. |

### Fechas, conteos y búsquedas

Los formularios reciben fecha y hora con precisión de minuto en Uruguay (UTC−3). El navegador convierte los extremos a UTC y suma un minuto al final; el servidor usa `desde <= fecha < hasta`. Así incluye el minuto final completo, sin depender de la zona horaria de la computadora. Fechas invertidas y fechas sin zona horaria son rechazadas por la API. Los atajos ofrecen 7, 30 y 90 días o todo el período.

Cada sección explica la fecha aplicada: registro o actividad de usuarios, creación o finalización de trabajos, intento de correo, creación de solicitudes de envío, recepción de contactos, creación de publicaciones, acciones administrativas y generación de recomendaciones. Los listados de operación y denuncias usan 25 registros por página, con límite de API de 100. Los totales de estado respetan período y búsqueda; se calculan antes del filtro de estado. Las categorías de cuentas habilitadas/confirmadas/con actividad se superponen y no deben sumarse como conjuntos disjuntos. Los datos corresponden a registros conservados.

El resumen cuenta los trabajos según su fecha de creación y estado actual; en Trabajos se puede elegir finalización para estudiar cuándo terminaron. La cola global de correos y la actividad de los últimos 15 minutos indican el estado actual de toda la plataforma y lo anuncian expresamente. El resto de métricas respeta el período seleccionado. Buscar usuarios usa nombre/correo; publicaciones, ID, nombre, descripción o autor; trabajos, modelo/código de error; contactos, nombre/correo/mensaje. La búsqueda usa parámetros y escapa comodines SQL.

**Mascotas recuperadas** cuenta avisos de pérdida con estado actual `FOUND`, creados en el período seleccionado. Se muestra junto a Publicaciones por tipo y en Estado de operación. Reconocer a la mascota en una coincidencia no basta: se cuenta cuando el dueño indica que la recuperó o marca su aviso como encontrado. Cada aviso cuenta una vez, aunque tenga varias coincidencias. Este filtro usa la creación del aviso, no la fecha en que se recuperó a la mascota.

Publicaciones por tipo cuenta registros: Avisos de pérdida incluye los recuperados y cerrados; Avistamientos cuenta reportes `USER_SIGHTING`; Reportes de mascotas encontradas cuenta publicaciones `FOUND_ANIMAL` recibidas desde Encontré una mascota. La recuperación de una mascota no crea un reporte de ese último tipo ni incrementa el total de publicaciones.

Las etiquetas tienen una «i» para consultar qué representa cada cifra o estado y cómo se aplica el período. También está disponible en los filtros, detalles de registros y seguimiento de coincidencias. Las ayudas explican la diferencia entre mascotas recuperadas y reportes de encontrados, tareas y publicaciones, envíos e intentos, cuentas habilitadas y actividad reciente. Abrir una ayuda no modifica filtros, estados ni datos.

### Actividad

`User.status = ACTIVE` indica una cuenta habilitada. La actividad se registra cuando una solicitud autenticada termina correctamente, también al iniciar sesión o crear una cuenta. Incluye las consultas automáticas del sitio. No certifica que la persona esté observando la pantalla ni mide duración de sesión.

`users.last_active_at` guarda el último minuto observado. `user_activity` conserva una fila por cuenta y minuto, sin IP, ubicación, ruta ni contenido; permite contar usuarios distintos que tuvieron actividad dentro del rango aunque hayan vuelto después. Una actualización condicional en la base evita duplicados entre procesos. Se escribe en una tarea posterior al envío de la respuesta, en una transacción independiente y con espera por bloqueo de fila limitada a 250 ms en PostgreSQL; un fallo de telemetría no invalida la autenticación ni los cambios del usuario. El modo de pruebas o una dependencia de base reemplazada desactiva esa escritura externa.

El historial se conserva 90 días; la última actividad de la cuenta persiste mientras exista la cuenta. El borrado de una cuenta elimina sus buckets mediante cascada. No se fabrican registros de actividad anteriores a la actualización.

### Correos y contactos

`email_delivery_log` registra un intento de entrega desde alertas, confirmación, recuperación, cambio de correo, recordatorio de fotos y reenvío de contactos. Cuando varias alertas se agrupan en un solo mensaje, se cuenta un envío y se indica cuántos elementos agrupó. `SENT` significa aceptado por SMTP; no confirma entrega al buzón, lectura, rechazo posterior o spam. `PREVIEWED` nunca se suma a enviados. `FAILED` cuenta intentos fallidos, incluidos los que se enviaron en un reintento posterior.

Se conservan 90 días de estos registros. El registro contiene tipo, estado, fecha, referencias de solicitudes y vínculo opcional a la cuenta. No copia correo destinatario, contenido, HTML, URL de recuperación, token de confirmación, contraseña o credenciales SMTP. Si se elimina la cuenta, el vínculo queda nulo. La interfaz muestra su nombre actual si la cuenta existe, sin presentarlo como una dirección histórica. El historial de intentos comienza con esta actualización: no se reconstruyen cantidades de mensajes antiguos a partir de notificaciones agrupadas ni se inventan fechas de envío.

La cola usa las solicitudes originales y muestra pendientes/fallidas con intentos y próxima disponibilidad. Omite alertas leídas, archivadas o inactivas y tokens consumidos/vencidos. Cuenta solicitudes, no futuros correos. El envío conserva sus reintentos existentes; este panel no ejecuta reenvíos ni nuevas comunicaciones.

Los contactos reenviados conservan la política existente: se eliminan de la base 30 días después de enviarse o previsualizarse. Pendientes y fallidos permanecen disponibles. Sus cifras describen los contactos conservados, no un total histórico perpetuo. La dirección indicada por el visitante no está verificada.

### Bloqueos

Bloquear una cuenta revoca sus sesiones y oculta sus avisos, avistamientos y encontrados. Se solicita nuevamente la comparación de las publicaciones afectadas. La cuenta administradora no puede bloquearse a sí misma; la API comprueba esto. Reactivar permite una nueva sesión, sin revivir las sesiones revocadas ni restaurar automáticamente las publicaciones.

Ocultar una publicación conserva sus datos y excluye su visibilidad pública y comparación. Restaurar verifica que su autor esté habilitado; esta comprobación también se aplica a restauraciones desde denuncias. Los reportes anónimos pueden ocultarse/restaurarse, pero no tienen una cuenta que bloquear. Ocultar/restaurar no cambia el estado de búsqueda activa, recuperada o cerrada.

Las nuevas acciones directas piden motivo y confirmación y registran estado anterior/nuevo y actor en `admin_audit`, en la misma transacción. Las acciones originadas en una denuncia conservan la referencia y motivo de denuncia. Los controles no eliminan cuentas ni publicaciones.

## Coincidencias y respuestas

Una recomendación es una pareja única de aviso y observación. En comparación general se registra cuando supera los filtros de candidatos; desde una ficha, cuando el motor declara `POSSIBLE_MATCH`. Una pista pendiente, incompatible, sin foto o de mascota bajo cuidado no se convierte por su mera recepción en una recomendación automática.

| Resultado | Criterio |
| --- | --- |
| Confirmadas | Última respuesta del dueño `RESOLVED`: reconoció a su mascota. No exige recuperación física. |
| Falsas | Última respuesta `FALSE_MATCH`. |
| Dudosas | Última respuesta `CONFIRMED_RELEVANT`: todavía no confirma identidad. |
| Sin respuesta | No hay una respuesta de las categorías anteriores. |

Se cuenta una vez cada pareja, usando la última respuesta humana. Los recálculos no reemplazan esa respuesta ni vuelven a contar la recomendación. La tasa de confirmación utiliza confirmadas / (confirmadas + falsas); sin denominador no hay porcentaje. No mide omisiones del modelo ni precisión sobre todos los casos: las respuestas son voluntarias y pueden tener sesgo.

`Match` conserva fecha, origen, puntaje y configuración de la primera recomendación. `match_feedback_events` conserva cambios de respuesta dentro de la transacción del aviso. Los datos recuperados de registros anteriores se identifican como históricos, sin inventar transiciones desconocidas. Cerrar/recuperar/ocultar conserva el seguimiento; eliminar los registros puede reducir sus totales.

El filtro temporal se refiere a la generación de la recomendación, no a la fecha del feedback. Se puede filtrar origen y registros nuevos/anteriores. El estado restringe la lista y no redefine silenciosamente el conjunto de indicadores. La lista pagina de a 25; el historial muestra las últimas 50 respuestas. Rutas privadas: `GET /api/v1/admin/matching` y `GET /api/v1/admin/matching/{id}/history`.

## Presentación y recarga

El dashboard ocupa todo el ancho disponible, con navegación lateral y menú adaptable a móvil. La preferencia claro/oscuro se conserva localmente y no cambia el tema público. Los gráficos usan datos consultados; sin datos muestran un estado vacío. No hay porcentajes de crecimiento ficticios.

Las etiquetas y filtros incluyen una «i» con definición y alcance temporal. Se abre con puntero, foco o toque y se cierra con Escape o fuera. Las ayudas no alteran filtros ni ejecutan acciones.

El botón circular flotante **Recargar datos** permanece visible durante el scroll, con icono y nombre accesible sin texto visible. Vuelve a consultar la sección sin recargar la página; conserva filtros, pestañas, paginación e historiales. En analytics fuerza un nuevo cálculo del mismo filtro y reemplaza la caché. Evita solicitudes manuales simultáneas y respeta movimiento reducido.

El período se comparte entre secciones; cada tabla informa qué fecha filtra. Los temas y la disposición se mantienen en los componentes de `apps/web/app/admin` y [globals.css](../apps/web/app/globals.css).

## Datos, rutas y mantenimiento

Los modelos operativos incluyen actividad por minuto e historial SMTP; no reconstruyen un pasado que no fue registrado. Aplicar las migraciones completas de la revisión antes de iniciar API y workers con ella. No se documenta como paso vigente una migración aislada de una entrega anterior.

Las consultas operativas utilizan `/api/v1/admin/operations` y sus listados de usuarios, trabajos, correos, cola, contactos, publicaciones y auditoría. Las mutaciones de visibilidad utilizan las rutas autorizadas de publicaciones o denuncias. Ver [routers](../apps/api/app/routers), [dependencias de acceso](../apps/api/app/dependencies.py), [métricas](analytics.md) y [operación del servidor](production.md).
