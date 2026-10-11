# Administración: seguimiento de coincidencias

## Acceso exclusivo

`/admin` exige sesión vigente, cuenta activa, correo confirmado, rol administrativo y la asignación única de `admin_access`. La API comprueba estas condiciones en todas las rutas administrativas, incluidas las reseñas. La tabla admite una sola fila, con `id = 1`, y una cuenta asignada. La navegación ofrece el enlace desde Mi cuenta solo cuando `/auth/me` devuelve `admin_access: true`. La ausencia de una asignación mantiene el acceso cerrado.

La asignación se administra desde el servidor con `python -m app.admin`, por entrada interactiva. No hay una ruta web para otorgar privilegios. Si la cuenta indicada aún no existe o no confirmó el correo, se reserva la dirección en la base privada. La confirmación válida de esa dirección vincula la cuenta y activa el acceso; una dirección escrita en un formulario o un rol aislado no bastan. También se reconoce la confirmación realizada mediante un enlace válido de recuperación. Una vez vinculada, la identidad es el UUID de la cuenta: el cambio verificado de contacto conserva su identidad. Eliminar la cuenta elimina su asignación y mantiene el acceso cerrado, sin reasignarlo automáticamente.

En el despliegue nuevo se debe repetir la reserva en su base de producción. La reserva local no se publica en Git ni se transfiere automáticamente a una base distinta. En Compose local:

```powershell
cd "C:\Users\jmoli\OneDrive\Escritorio\buscadorMascotas"
docker compose exec api python -m app.admin
```

## Qué se cuenta

- Una recomendación es una pareja única de aviso perdido y reporte observado.
- En búsqueda general se registra al superar los filtros y el umbral para candidatos.
- Desde una ficha se registra cuando la comparación declara `POSSIBLE_MATCH`. La recepción de una pista pendiente, incompatible o sin foto no se cuenta como recomendación automática.
- **Confirmadas:** el dueño respondió `RESOLVED`, que en la interfaz corresponde a reconocer a su mascota. Recuperarla también confirma esa identidad, pero sigue siendo una sola recomendación.
- **Falsas:** el dueño respondió `FALSE_MATCH`.
- **Dudosas:** respondió `CONFIRMED_RELEVANT`; todavía no confirma la identidad.
- **Sin respuesta:** no existe una respuesta del dueño entre los tres estados anteriores.

Se usa la última respuesta de cada pareja desde el historial del dueño, sin sumar nuevamente al cambiarla. Los recálculos de estado del motor no reemplazan esa respuesta. El porcentaje de confirmadas se calcula únicamente sobre confirmadas más falsas; si ese denominador es cero, no se muestra un porcentaje. El porcentaje de respondidas incluye las dudosas. Estas cifras describen las respuestas recibidas: no son una precisión medida sobre todos los casos, no cuentan las coincidencias omitidas y pueden tener sesgo de participación.

Cerrar, recuperar u ocultar una búsqueda conserva su seguimiento. Eliminar sus registros elimina las recomendaciones y su historial por las mismas cascadas de la publicación; los totales corresponden a datos conservados, no a un registro perpetuo de cuentas eliminadas.

## Persistencia y migración

`0020_admin_matching` agrega fecha, origen, puntaje y configuración de la primera recomendación a `matches`; los recálculos posteriores no reemplazan esa fotografía del momento. La configuración incluye modelos, versiones de prompts, versión del seguimiento y umbrales, sin contactos ni imágenes. `match_feedback_events` conserva los cambios de respuesta y las recuperaciones dentro de la misma transacción que modifica el aviso y las notificaciones. Las estadísticas cuentan parejas, no eventos. Los permisos no se obtienen desde los datos de registro.

La migración recupera la respuesta vigente de los casos anteriores cuando existe `feedback_at`. Marca el historial recuperado como anterior, sin inventar transiciones o recuperaciones. Puede reconstruir las recomendaciones generales y las vinculadas que aún están como `POSSIBLE_MATCH`; otras sugerencias antiguas ya recalculadas no se pueden reconstruir con certeza. Los puntajes y fechas anteriores se marcan como datos recuperados del estado disponible. El filtro de registros permite excluirlos.

Filtros: fecha y hora de Uruguay con extremos de minuto y atajos de 7, 30 o 90 días, o todo el período; origen general o desde una ficha; registros nuevos o anteriores; y estado para la lista. El período se refiere a la generación de la recomendación, no a la fecha de la respuesta. El filtro de estado solo afecta la lista: los indicadores conservan el conjunto seleccionado por período, origen y tipo de registro. Se muestran 25 recomendaciones por página y las últimas 50 respuestas al abrir un historial. Los horarios se presentan en Uruguay. La ampliación de usuarios, trabajos, correos y moderación se describe en [admin-operations.md](admin-operations.md).

Rutas privadas: `GET /api/v1/admin/matching` y `GET /api/v1/admin/matching/{id}/history`. Todas las respuestas usan `Cache-Control: no-store`; los proxies web conservan la autorización de la cookie y solo aceptan las rutas y parámetros previstos.

## Layout Structure

La página conserva el ancho de 1280 px y el sistema de márgenes del sitio. Los filtros se distribuyen en columnas adaptables de al menos 230 px; los cinco indicadores, en columnas de al menos 185 px. Cada bloque ocupa una columna en pantallas pequeñas y crece con el contenido.

## Section Order

Título e introducción, sesión, selector de sección, filtros, indicadores, proporción de confirmadas, desglose por origen, lista e historial. Gestión de la plataforma conserva denuncias, registros, fallos y auditoría en la segunda sección.

## Navigation

Tres botones permiten alternar entre operación, seguimiento de coincidencias y denuncias/correcciones. Los filtros reinician la paginación. La lista tiene anterior y siguiente; cada historial se abre en la propia tarjeta. Mi cuenta ofrece el acceso solo a la cuenta autorizada.

## Typography

Arial y los encabezados existentes. Los indicadores usan 36 px y la proporción, 40 px; las etiquetas, 14 px; ayudas, 13 px. Los números usan cifras tabulares para facilitar la comparación.

## Color System

Se conservan azul oscuro, blanco y crema. Verde para confirmadas, coral para falsas, ámbar para dudosas y azul para pendientes. Todos los estados tienen texto y cantidades; el color es un refuerzo.

## Spacing and Layout Rhythm

Bloques separados por 24 px; filtros, análisis y tarjetas con 24 px interiores; indicadores con 20 px; rejillas con 16 px de separación. La navegación tiene controles de al menos 48 px.

## Image Treatment

El panel utiliza datos, sin fotografías ni ilustraciones. La lista presenta IDs y nombres de mascotas, sin contactos o coordenadas precisas. Esto permite revisar respuestas sin cargar imágenes privadas innecesariamente.

## Cards and Content Blocks

Tarjetas blancas con borde existente, radios de 14–16 px y fondos suaves en los indicadores. Una barra proporcional resume los estados, con una descripción accesible. La tabla de origen se desplaza dentro de su contenedor en pantallas pequeñas.

## Buttons and CTAs

Actualizar y paginación usan botones secundarios del sitio. Los historiales usan botones de texto con estado expandido. Los cambios de gestión mantienen sus controles existentes.

## Overall Design Feel

Un panel claro y sobrio que prioriza cantidades, respuestas y contexto. Las confirmaciones, dudas y falta de respuesta se distinguen sin presentar los resultados como una probabilidad de identificación.

## Revisión de la entrega

La migración se aplicó sobre la instalación local y se configuró la cuenta indicada mediante la reserva privada. La cuenta quedó vinculada y habilitada tras su confirmación. TypeScript, la sintaxis Python, los modelos y las rutas cargaron correctamente. La consulta y la vista autenticada mostraron dos recomendaciones anteriores: una confirmada y una dudosa. También se abrió su historial existente desde el panel. El contenido se adaptó al ancho disponible sin desbordamiento del panel; se guardó una captura de los indicadores.

Se ajustó la preparación administrativa de las comprobaciones existentes para representar una cuenta confirmada con la asignación única. No se añadieron ni ejecutaron pruebas automatizadas, crearon casos de muestra, cambiaron respuestas de dueños o enviaron correos de prueba durante esta entrega.
