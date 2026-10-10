# Reseñas de la comunidad

## Solicitud y publicación

- Después de **Cerrar aviso** o **Marcar como encontrado** en Mis avisos, el estado se guarda y se muestra una invitación independiente y opcional a escribir una reseña.
- Después de **Ya la recuperé** desde una notificación, se conserva la invitación fuera de la alerta que acaba de retirarse. Confirmar **Es mi mascota, sigo buscándola** no solicita reseña y mantiene la búsqueda activa.
- Los avisos propios en estado `FOUND`, `CLOSED` o `CANCELLED` muestran la invitación al volver a Mis avisos. Si ya hay una reseña, se muestra su estado y la opción de retirarla.
- **Ahora no** permite omitir la invitación y **Cancelar** permite salir del formulario sin afectar el aviso. Escribir una reseña no cambia el estado ni el matching.

El formulario pide de 1 a 5 estrellas, un comentario de 20 a 800 caracteres y autorización explícita para mostrar la reseña en la portada. El nombre público es opcional, admite un apodo y no se rellena desde la identidad de la cuenta: vacío significa **Anónimo**. No se publican correo, IDs de cuenta/aviso, contacto, fotos ni ubicación.

Solo el dueño del aviso, con cuenta activa y correo confirmado, puede publicar. El servidor comprueba la titularidad y que el aviso esté cerrado o la mascota encontrada; no confía en el estado enviado por la web. El formulario conserva el texto al confirmar el correo en otra pestaña. La unicidad por aviso y el bloqueo de escritura evitan reseñas duplicadas por doble envío; también se aplican los límites generales de publicación.

## Portada

`HomeReviews` consulta la lista pública y no renderiza encabezado, espacio ni mensaje vacío cuando no hay reseñas. La sección se ubica después de los avisos activos y antes del bloque Apoyanos. Muestra hasta seis reseñas recientes, sin filtrar por puntuación ni inventar testimonios, estrellas, nombres o resultados de búsqueda. Cada tarjeta muestra el comentario completo, las estrellas, el nombre elegido y el mes/año.

Se incluyen solo reseñas visibles de cuentas activas con correo confirmado y avisos retirados que no estén ocultos por moderación. Reabrir una búsqueda retira temporalmente su reseña de la lista pública; cerrarla de nuevo permite mostrar la misma reseña, sin crear otra. La consulta evita caché; la portada actualiza al cargar y recuperar el foco. Un fallo de carga también oculta la sección.

## Retirada y administración

**Retirar mi reseña de la portada** cambia su visibilidad a `WITHDRAWN`; conserva un registro privado y no vuelve a pedirla ni permite restaurarla desde administración. Las reseñas se consultan en `/admin` → Registros de la plataforma → Reseñas, donde se pueden ocultar/restaurar las demás. Las acciones administrativas se auditan. El bloqueo de la cuenta o la eliminación definitiva del aviso también retiran su reseña pública; el borrado del aviso elimina la reseña mediante su clave foránea.

## Rutas

| Método | Ruta de API | Acceso |
| --- | --- | --- |
| GET | `/api/v1/public/reviews?limit=6` | Público; máximo 12 |
| GET | `/api/v1/reviews/lost-cases/{case_id}` | Dueño; elegibilidad y reseña propia |
| POST | `/api/v1/reviews/lost-cases/{case_id}` | Dueño con correo confirmado; una por aviso |
| DELETE | `/api/v1/reviews/lost-cases/{case_id}` | Dueño; retirada de portada |
| GET | `/api/v1/admin/records/reviews` | Administrador |
| PATCH | `/api/v1/admin/reviews/{review_id}` | Administrador; ocultar/restaurar |

La web usa el proxy `/api/reviews`, la cookie de sesión existente, validación de origen en escrituras y cuerpos acotados. El texto se renderiza como contenido de React, sin interpretar HTML. La migración `0014_case_reviews` agrega una tabla y no genera reseñas ni altera los avisos anteriores. El inicio de la API aplica la migración.
