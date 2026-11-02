# Avisos compactos, características y búsqueda

## Layout Structure

`/perdidos` conserva el ancho general del sitio y su grilla de avisos. Los filtros principales se distribuyen en tres columnas y pasan a dos en celular. La búsqueda ocupa una fila completa. Las cards tienen una foto de proporción 8:5 y contenido más compacto.

## Section Order

Título y publicación, búsqueda y filtros, resultados, paginación y footer. Los filtros adicionales se despliegan dentro del buscador. En formularios se indican primero mascota, nombre cuando corresponde, sexo y tamaño; luego raza, colores y accesorios, antes de la descripción y las fotos.

## Navigation

Las flechas, los indicadores de foto y las teclas izquierda/derecha cambian la imagen dentro de la card. En pantallas táctiles también se puede deslizar. La foto y “Ver aviso” abren la publicación; ampliar muestra la foto seleccionada en el visor. El formulario vinculado mantiene lugar, fecha y fotos como recorrido breve, con características en una sección opcional.

## Typography

Se conservan las fuentes del sitio. Los nombres usan 21 px en las cards; la información usa 12–13 px y el ID 11 px, junto al estado. Los ID conservan texto accesible y los lugares largos ocupan hasta dos líneas. La descripción completa se consulta dentro del aviso.

## Color System

Se mantienen coral, azul oscuro y fondos suaves existentes. Los colores escritos por una persona se muestran como texto; las etiquetas conocidas siguen traducidas al español. Las sugerencias de raza cambian entre perro y gato, admitiendo siempre una entrada libre.

## Spacing and Layout Rhythm

Las cards usan 14 × 16 px de espacio interior, márgenes reducidos y una sola fila de estado e ID. Las características y las ubicaciones extensas se limitan a dos líneas en la lista. Los controles táctiles principales conservan 44 px de área.

## Image Treatment

Se muestra primero la miniatura elegida, incluyendo fotos heredadas de la mascota. Las imágenes se ajustan sin recortarlas en el carrusel. La lista recibe los ID de las fotos en lote, evitando consultar un álbum separado por cada card. El visor admite fallos de carga y las cards sin fotos muestran el estado correspondiente.

## Cards and Content Blocks

Raza, color principal, hasta cinco colores secundarios, presencia de collar, color y detalles del collar, presencia de prenda/accesorio, tipo y color se guardan en campos independientes de la descripción original. Los campos nuevos son opcionales en creación y edición de pérdidas, avistamientos y mascotas encontradas. Los detalles se muestran en la publicación y en la vista pública del avistamiento.

## Buttons and CTAs

Buscar y Aplicar filtros conservan los valores elegidos y reinician la paginación. Limpiar filtros restaura el listado. Los controles del carrusel tienen etiquetas accesibles y no navegan al aviso. En las vistas con copia de ID, se usa un pequeño botón con el mismo sistema de iconos del sitio.

## Overall Design Feel

La presentación conserva el estilo de MascoMatch y reduce la altura de cada resultado. Las opciones avanzadas se despliegan cuando hacen falta. Los accesorios muestran sus campos de detalle al indicar que están presentes.

## Contrato y operación

- Migración aditiva: `0032_report_details`, posterior a `0031_donations`. Se respaldó la base local antes de aplicarla. No modifica descripciones, fotos, ID ni estados existentes.
- Los filtros se combinan antes del conteo y la paginación: `q`, `species`, `breed`, `color`, `lost_from`, `lost_to`, `sex`, `size`, `with_photos`, `collar`. Las fechas incluyen el día completo en `America/Montevideo`. Se rechazan rangos invertidos.
- La búsqueda por color considera principal y secundarios, incluidos valores libres y acentos. Raza y color usan búsqueda parcial y escapan comodines de SQL. Los filtros mantienen las restricciones de cuenta activa, aviso activo, moderación visible y especie admitida.
- Los colores sugeridos conservan sus valores canónicos; los libres se guardan recortando espacios. Una edición parcial no borra campos omitidos. Indicar explícitamente ausencia de collar/prenda elimina sus detalles asociados.
- Un avistamiento vinculado admite `details` JSON opcional; los valores observados no se copian del aviso. La huella de reintento incluye detalles informados y conserva compatibilidad cuando están vacíos.
- Los nuevos campos se incluyen en las entradas de análisis cuando tienen información. Los valores vacíos no invalidan las huellas históricas. Un color libre no genera por sí solo una contradicción categórica contra un color general del modelo.
- Las respuestas públicas siguen usando campos permitidos explícitos, sin contactos, coordenadas precisas ni claves de almacenamiento.

## Verificación

Pruebas de creación y edición de los tres tipos de reporte, datos libres, accesorios, reintentos de avistamientos breves, búsquedas combinadas, paginación, fechas de Uruguay, colores con acentos, privacidad y orden de fotos heredadas/miniatura. También se verificaron coincidencias y análisis existentes, TypeScript, pruebas web y la interfaz en escritorio y celular.

## Acciones dentro de un aviso

Cada publicación ofrece “La vi” y “La tengo conmigo”. La primera abre `/avistamiento?aviso=ID` y la segunda `/encontre?aviso=ID`. Ambas conservan el formulario breve de lugar, fecha y fotos opcionales; cambiar de opción desde el cartel de ayuda conserva el aviso vinculado. `/encontre` sin aviso sigue abriendo el formulario general existente.

El envío vinculado acepta `source_type=USER_SIGHTING` (predeterminado compatible con solicitudes anteriores) o `FOUND_ANIMAL`. El tipo encontrado se incorpora a la huella del envío para evitar reutilizar la misma solicitud como avistamiento. La notificación y el correo al dueño explican que la persona indicó tener la mascota bajo su cuidado; la identidad sigue por confirmar y el aviso continúa activo hasta que el dueño confirme el reencuentro. Se conserva la opción de enviar el reporte breve sin cuenta.
