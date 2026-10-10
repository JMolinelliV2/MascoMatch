# Lectura y archivo de notificaciones

La bandeja abre en **Sin leer**. Marcar una alerta como leída la retira de esa vista y permite consultarla en **Todas**. **Archivar notificación** la quita de ambas y la conserva en **Archivadas**, con **Restaurar notificación** para volver a Todas. Restaurarla conserva la fecha de lectura y no vuelve a enviar el correo.

Las tarjetas indican **Sin leer**, **Leída** o **Archivada**, con la fecha de lectura en horario de Uruguay. **Abrir alerta** y los enlaces de correo llevan al detalle; al cargarlo con la cuenta del dueño, se marca como leído automáticamente. Consultar el listado no marca de golpe alertas que el usuario todavía no abrió. La acción **Marcar todas como leídas** procesa todas las páginas de la bandeja, conservando los avisos posteriores a la solicitud.

## Persistencia y permisos

- La migración `0018_notification_archive` incorpora `Notification.archived_at`. No elimina registros existentes ni marca automáticamente las alertas previas.
- `read_at` conserva su primera fecha mediante `coalesce`; repetir la operación no la cambia. Archivar también marca como leída, conservando fechas previas.
- El archivo se guarda por separado de `is_active`, que sigue representando la disponibilidad del aviso o comparación. Una nueva evaluación de IA no borra el archivo ni la lectura. Nuevos avistamientos generan sus propias alertas.
- `GET /notifications?view=unread|all|archived` filtra en el servidor y pagina cada vista. `unread_count` siempre cuenta alertas elegibles, sin leer y sin archivar. El valor predeterminado de la API sigue siendo `all` por compatibilidad; la web pide `unread` al abrir la bandeja.
- `PATCH /notifications/{id}/read`, `/archive` y `/restore` verifican dueño, aviso y visibilidad. `PATCH /notifications/read-all` utiliza ese mismo alcance, con una fecha de corte. No permite modificar alertas de otra cuenta.
- El proxy web mantiene la sesión privada y la comprobación de origen para las cuatro acciones. Todos los resultados son `no-store`.
- Archivar no altera el aviso, el avistamiento, las fotos ni el resultado de la comparación. Las fotos de una alerta archivada conservan los mismos permisos de dueño. Los avisos cerrados u ocultos continúan fuera de estas vistas, como antes.

## Actualizaciones y correo

La web bloquea acciones de bandeja simultáneas, invalida consultas anteriores al guardar y pausa el refresco durante la operación. Una respuesta iniciada antes de marcar como leída no puede sobrescribir el estado guardado. Después del resultado, la lista y el contador del encabezado consultan los valores actuales. Al retirar el último elemento de una página, se ajusta la paginación.

Los resultados se confirman después del éxito del servidor. Un fallo conserva la tarjeta y muestra el error. La lectura automática se intenta una vez por apertura de detalle; si falla, permanece la acción manual.

Marcar como leída o archivar cancela un correo que todavía esté pendiente. La cola vuelve a comprobar lectura y archivo antes de agrupar mensajes, y las métricas de operación excluyen esas alertas. Los correos ya enviados conservan su estado; un mensaje que ya está siendo enviado puede completar su entrega.

## Revisión del 10 de octubre de 2026

TypeScript y la sintaxis Python terminaron sin errores. La API local aplicó `0018_notification_archive`; las consultas de lectura de las tres vistas mostraron una alerta existente sin leer, la misma en Todas y cero archivadas, con el nuevo campo de archivo. No se marcaron ni archivaron alertas reales para la revisión. No se agregaron ni ejecutaron pruebas automatizadas ni se iniciaron sesiones o enviaron correos.
