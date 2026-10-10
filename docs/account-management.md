# Gestión de cuenta

`/mi-cuenta` permite editar nombre, teléfono opcional y correo. El acceso Mi cuenta del encabezado lleva a esta página; Mis avisos conserva sus publicaciones, edición, coincidencias y cierre.

## Cambio de contacto

Nombre y teléfono se guardan inmediatamente. Cambiar el correo requiere la contraseña actual y genera un enlace de un solo uso, válido durante 24 horas, enviado a la nueva dirección. Hasta confirmarlo, el correo actual sigue siendo la dirección de ingreso y de las alertas. La dirección pendiente no reserva una cuenta: su disponibilidad se vuelve a comprobar mediante la restricción única de la base al confirmar.

El usuario puede reenviar o cancelar el cambio desde Mi cuenta. Se aplican los límites existentes de enlaces (un minuto entre solicitudes y tres por hora por cuenta) y de intentos de contraseña. Confirmar el cambio invalida los enlaces de acceso pendientes y todas las sesiones anteriores; hay que ingresar con el nuevo correo y la contraseña habitual. Los enlaces de cambio están asociados a su destinatario para evitar que un enlace anterior confirme otra dirección.

## Eliminación

La sección desplegable exige la contraseña y escribir ELIMINAR. `DELETE /auth/me` elimina físicamente el usuario, sus mascotas, todos sus avisos perdidos, reseñas, coincidencias, notificaciones, sesiones y enlaces de acceso. Los avistamientos y reportes de encontrados permanecen con `author_id=NULL` y `share_contact=false`, junto con sus fotos y análisis. Las observaciones asociadas a un aviso eliminado se desvinculan y quedan pendientes de comparación con otros casos.

Las fotos de mascotas y avisos eliminados desaparecen de la API en la misma transacción. Sus objetos privados quedan en `photo_deletions`, una cola persistida que el proceso de la API revisa cada diez segundos. Si el almacenamiento falla, reintenta con espera creciente hasta una hora; no abandona el borrado. Un rollback de la cuenta no elimina objetos del almacenamiento. Los respaldos históricos conservan su propia retención y no se modifican en este flujo.

La migración `0016_account_management` añade el correo pendiente, el destinatario de los enlaces y la cola de borrado. Las acciones de moderación conservan su historial con actor nulo cuando se elimina esa cuenta. El downgrade requiere que no haya actores ya eliminados; no reconstruye cuentas borradas.

Las mutaciones de mascotas, casos, observaciones y fotos bloquean primero la cuenta con `FOR NO KEY UPDATE`, para serializar la eliminación sin bloquear las referencias de avistamientos anónimos. La eliminación bloquea después las mascotas y los casos antes de retirar sus datos. Los avistamientos breves sin cuenta siguen admitidos.

El navegador utiliza un proxy con cookie HttpOnly, validación del origen, rutas permitidas y límite del cuerpo. La contraseña no se devuelve, persiste ni registra en estas rutas.

## Revisión de esta entrega

Se revisan tipos y sintaxis, el inicio de los servicios y las páginas en lectura. No se eliminan cuentas reales, cambian contactos, envían solicitudes de correo ni publican reportes para revisar esta implementación. No se ejecutan pruebas automatizadas en esta entrega.
