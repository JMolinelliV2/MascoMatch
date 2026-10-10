# Rediseño de MascoMatch

Las cuatro referencias visuales se adaptan al flujo existente. Se conserva la marca MascoMatch, los tres pasos de los formularios generales y el avistamiento breve desde una ficha. Se mantienen las rutas, los campos, las validaciones y los contratos de la API.

## Layout Structure

Contenedor de 1280 px con márgenes automáticos y 24 px laterales. Portada con texto y foto en dos columnas. Formularios con una columna principal flexible y ayuda lateral de 320 px; bajo 950 px pasan a una columna. Desde 360 px los controles se apilan, el stepper muestra la etapa activa y las fotos se pueden recorrer horizontalmente.

Cómo funciona ocupa una sección propia, con título visible, introducción y cuatro pasos en una grilla de dos columnas. A 640 px o menos se apila en una columna. La altura mínima en escritorio es 72 vh y el contenido puede crecer; en móvil se usa altura natural.

Apoyanos utiliza el contenedor de 1280 px y una introducción centrada de hasta 780 px. Los cuatro niveles ocupan cuatro columnas, dos a 950 px o menos y una a 640 px o menos. El monto personalizado, el resumen y las acciones se apilan en móvil. El destino de los aportes usa tres columnas en escritorio y una en móvil.

Las reseñas de portada usan el mismo contenedor, tres columnas en escritorio, dos bajo 950 px y una bajo 640 px. Sin reseñas visibles el componente devuelve `null`, por lo que no agrega espacio ni encabezado vacío.

## Section Order

Portada: navegación, presentación y acciones para los tres tipos de reporte, Cómo funciona, avisos activos reales, acceso al mapa, bloque de apoyo y pie con atribución de la fotografía. Cómo funciona explica publicación y confirmación de correo, aportes de la comunidad, revisión de posibles coincidencias y cierre después del reencuentro; termina con consejos de fotos, lugar y fecha y acceso a los animales publicados. Formularios: título, tres etapas, campos del paso actual, validación, acciones y ayuda. Mis avisos: sesión, dos cantidades derivadas de los datos, casos con controles, reportes enviados y acceso a notificaciones.

Apoyanos: regreso al inicio, presentación, aviso de disponibilidad próxima, frecuencia del aporte, niveles, monto personalizado, resumen, destino de los aportes, preguntas frecuentes y acción para explorar animales perdidos.

La portada incorpora las reseñas después de los avisos y el acceso al mapa, antes de Apoyanos. En Mis avisos y Notificaciones, la invitación aparece después de guardar el cierre o la recuperación del animal y se mantiene separada del estado de la búsqueda.

## Navigation

Logo a la izquierda; Inicio, Perdí una mascota, Vi una mascota y Mis avisos en el centro; botón Apoyanos, notificaciones y cuenta a la derecha. Mis avisos y Notificaciones se muestran con sesión iniciada. Explorar conserva Animales perdidos, Mapa, Encontré una mascota y el enlace a `#como-funciona`. Apoyanos tiene un botón propio con corazón, borde y fondo coral suave; está fuera de los desplegables y disponible sin sesión. La ruta activa usa subrayado coral y `aria-current`. Bajo 1100 px la navegación se reúne en un menú nativo para dejar lugar a los accesos visibles. Bajo 640 px Apoyanos ocupa una segunda fila del encabezado, sin esconderse dentro del menú.

La reseña se escribe dentro de Mis avisos o de la pantalla de la notificación de recuperación, sin cambiar de página. El autor vuelve a ella desde Mis avisos para retirarla; administración agrega la categoría Reseñas a los registros existentes.

## Typography

Se conserva Arial, la fuente existente, sin añadir descargas externas. Títulos de página de 32–46 px y peso 800; portada de hasta 58 px; secciones de 22–26 px; tarjetas de 18–22 px; texto de 14–16 px y ayudas de 12–13 px. El contenido largo permite salto de línea.

El título de Cómo funciona usa 28–36 px, la introducción 16–17 px, los títulos de pasos 20–21 px y su texto principal 15 px. Los detalles complementarios se separan con una línea y usan 13 px.

Apoyanos mantiene los títulos generales, encabezados de sección de 24–28 px y niveles de 21 px. Los importes usan 30 px y peso 800, con frecuencia de 13 px. Las descripciones usan 15 px y los detalles de destino 13 px.

Las reseñas usan texto principal de 15 px con interlineado 1,7, nombre público de 14 px y fecha de 12 px. El formulario tiene título de 18 px y campos de 14–16 px. Los comentarios completos conservan saltos de línea y permiten cortar palabras largas para evitar desbordamientos.

## Color System

Variables semánticas en `globals.css` y colores equivalentes en el tema Tailwind. Fondo cálido, superficies blancas y texto navy. Coral para acciones principales; azul para información, ubicación y foco; verde para encontrado o compatibilidad alta; amarillo para revisión y advertencias. El coral se oscurece respecto de la referencia para mejorar el contraste del texto blanco. Los estados también llevan texto y no dependen solo del color.

El nivel elegido lleva borde coral de 2 px, fondo coral suave, check y texto Elegido. El resumen usa fondo azul suave. El botón de pagos pendientes es gris y está deshabilitado; no se presenta como una operación en curso.

Las estrellas y la puntuación seleccionada usan coral, con texto accesible que informa de 1 a 5 estrellas. La invitación a reseñar usa fondo azul suave, separado de los mensajes de cierre ya guardado.

## Spacing and Layout Rhythm

Separaciones de 8, 12, 16, 20, 24, 28 y 32 px. Tarjetas con 24–28 px de padding en escritorio y 16–20 px en móvil. Campos de al menos 48 px y acciones táctiles de al menos 44 px. Ayudas y revisión conservan una jerarquía separada de los campos.

Cómo funciona tiene 64 px de separación superior y 72 px inferior en escritorio, tarjetas de al menos 240 px y gaps de 24 px. En móvil el padding vertical es 48 px y los pasos crecen según su contenido, sin recortar texto ni forzar espacio vacío.

Los niveles de apoyo usan gaps de 20 px y padding de 24 px; el resumen, 24–28 px. La sección de destino empieza 64 px después del selector, reducidos a 48 px en móvil. El bloque de apoyo en portada usa padding de 28 px y una separación inferior de 40 px.

La grilla de reseñas usa gaps de 20 px y tarjetas con padding de 24 px, reducido a 20 px en móvil. La invitación tiene margen superior de 24 px y padding de 20 px. Puntuaciones y acciones conservan objetivos táctiles de 48 px.

## Image Treatment

La fotografía existente de portada conserva su atribución. Los avisos muestran únicamente fotos reales de la API, con un estado de ausencia cuando no hay foto. Miniaturas cuadradas y fotos de detalle de 4:3. El cargador compartido conserva una foto opcional para reportes generales y hasta cuatro para avistamientos vinculados, con JPEG, PNG y WebP de hasta 10 MB. Incluye selección, arrastre, miniaturas, eliminación y errores; no agrega campos al payload.

Apoyanos reutiliza los iconos SVG de corazón, huella, coincidencias y cuidado del proyecto. No añade imágenes remotas ni fotografías de supuestos reencuentros.

Las reseñas usan el corazón existente y estrellas de texto; no añaden avatares, fotografías ni imágenes del aviso. El nombre público elegido se muestra independientemente de la identidad privada de la cuenta.

## Cards and Content Blocks

Tarjetas blancas, bordes discretos, radios de 12–16 px y sombra mínima. Componentes compartidos para stepper, fotos, iconos, tarjetas de animales y compatibilidad. El panel muestra las cantidades disponibles en sus datos; no se inventan nuevos avistamientos, compartidos, historias o recorridos. La foto de un aviso activo respeta el endpoint público y sus restricciones.

Los cuatro pasos de Cómo funciona usan iconos existentes, un número visible y dos niveles de explicación. El bloque final de consejos usa fondo azul suave. El contenido distingue confirmar un avistamiento de recuperar al animal y explica el envío breve sin cuenta.

Los niveles de patrocinio son etiquetas de radios nativos: toda la tarjeta permite seleccionar, el teclado conserva el comportamiento del grupo y el foco tiene contorno azul. Nombre, importe, frecuencia y descripción tienen jerarquía propia. Las preguntas frecuentes usan `details` y `summary` nativos. No se muestran cantidades de donantes, metas ni testimonios ficticios.

Las tarjetas de reseñas son artículos con puntuación, cita y pie de autor/fecha. El formulario opcional tiene cinco radios nativos, nombre público, comentario, contador y consentimiento sin marcar inicialmente. Solo se muestran testimonios persistidos de dueños de avisos retirados.

## Buttons and CTAs

Acción principal coral, secundaria blanca con borde y terciaria azul con texto. Radios de 10–12 px. En móvil las acciones principales de publicación ocupan el ancho disponible. Todos los controles de cerrar, quitar foto o navegar tienen texto o nombre accesible. Se mantiene el bloqueo de controles durante las operaciones y el feedback de guardado, error y éxito.

El cierre de Cómo funciona enlaza al catálogo con **Ver animales perdidos** y al formulario existente con **Reportar un animal encontrado**. En móvil la acción al catálogo ocupa el ancho disponible.

La portada enlaza a **Conocé cómo apoyar**. En Apoyanos, **Donaciones próximamente** está deshabilitado y acompañado por la explicación de disponibilidad. Elegir un nivel no genera un cobro. La acción final **Ver animales perdidos** permite seguir participando sin aportar dinero.

La invitación ofrece **Escribir una reseña** y **Ahora no**. El formulario ofrece **Publicar reseña** y **Cancelar**. El cierre del aviso no depende de estas acciones. Una reseña guardada muestra **Retirar mi reseña de la portada**.

## Overall Design Feel

Herramienta clara y cercana, con fotografías como principal elemento emocional. No se agregan ilustraciones decorativas, métricas ficticias ni mensajes de identidad confirmada a partir de una puntuación. La compatibilidad se muestra con contexto y conserva la revisión humana.

La página de apoyo conserva ese estilo simple y presenta la donación como voluntaria. Los importes están identificados como UYU y los niveles no ofrecen prioridad en las búsquedas. El circuito de pagos queda pendiente, documentado en `donations.md`.

Las reseñas describen experiencias de búsqueda, sin asumir que un cierre implica reencuentro ni atribuir una recuperación a MascoMatch. Incluyen puntuaciones de todo el rango y admiten apodos o anonimato.

## Preservación de flujos

- Los pasos generales siguen siendo Mascota → Fecha y lugar → Contacto y revisión. Las fotos permanecen en el primer paso y no se agrega una etapa nueva.
- La búsqueda restringida por país, selección del lugar, mapa incrustado, movimiento del pin y precisión siguen utilizando los componentes y lógica existentes.
- El selector visual de sexo mantiene el `select` con nombre `sex` y valores `unknown`, `male` y `female` que utilizan la revisión y los payloads actuales.
- Se mantienen creación/ingreso de cuenta, privacidad del contacto, publicaciones sin foto, aviso cuando falla una foto y procesamiento posterior a publicar.
- El avistamiento vinculado conserva ubicación, hora y fotos opcionales, envío sin cuenta, identificador de solicitud y consulta posterior del estado.
- Mis avisos conserva edición, fotos, coincidencias, feedback, encontrado, cierre y reapertura. El mapa de última ubicación usa los datos privados del caso propio.
- La navegación conserva catálogo, mapa, notificaciones, recuperación, confirmación y administración mediante sus rutas existentes.
- Los avisos abiertos desde los puntos o la lista del mapa incluyen `origen=mapa` y muestran **Volver al mapa**. Los avisos abiertos desde el catálogo conservan **Volver a animales perdidos**. Solo se admite ese origen conocido, sin aceptar direcciones de regreso arbitrarias.

## Verificación

Las pruebas de componentes comprueban las tres etapas, el contrato de sexo, las fotos opcionales y el contexto de los scores. La compilación de producción confirma las rutas existentes. La revisión de navegador utiliza una instancia temporal de la API con SQLite, imágenes en memoria, correo e IA desactivados, y cuentas de prueba; no publica reportes de prueba en la base real.

### Resultado de la revisión del 9 de octubre de 2026

- Frontend: 31 pruebas aprobadas, TypeScript sin errores y compilación de la imagen de producción completada con las rutas existentes.
- API: 163 pruebas aprobadas y 4 omitidas en la suite aislada. No hubo cambios en código, modelos ni contratos del backend.
- Pérdida: validación por etapa, selección y eliminación de foto, reselección del mismo archivo, Atrás sin perder datos, sexo en la revisión, ingreso con cuenta existente y publicación con foto.
- Ubicación: sugerencias restringidas a Uruguay, mapa incrustado y movimiento del pin con teclado, conservado al volver entre etapas.
- Avistamiento vinculado: envío sin cuenta ni foto; alerta privada al dueño, mapa de la alerta, marcado como leída y feedback guardado. La opción de indicar una hora aproximada conserva el formulario breve.
- Avistamiento general: publicación sin foto y con ubicación; las coincidencias aparecen después de guardar, con características, fecha y distancia como explicación.
- Encontrado: publicación sin foto ni ubicación, conservando los datos opcionales y el tipo de reporte diferenciado en Mis avisos.
- Mis avisos: edición guardada, cierre, reapertura, marcado como encontrado, nueva reapertura y mapa de última ubicación dentro de la página.
- Catálogo: búsqueda sin resultados y regreso a todos los avisos. Mapa comunitario: puntos reales, colores resueltos desde los tokens y filtro de capas que actualiza la cantidad visible.
- Móvil: navegación y formularios revisados a 360 × 800 px, sin desbordamiento horizontal. Campos y acciones principales de 48 px; pin y controles de zoom de 44 px; mapa de 240 px de altura. Los errores se muestran junto al campo y se relacionan con `aria-describedby` y `aria-invalid`.
- Contraste calculado sobre blanco: acción coral con texto blanco, 4,60:1; texto de ayuda, 4,76:1; borde de controles, 3,04:1. La selección de sexo incluye un check y el estado accesible del control.
- La base local real conserva los mismos registros: 2 avisos, 0 avistamientos, 1 foto y 1 embedding.
- Portada local: avisos reales con y sin foto, revisados en escritorio y móvil. Las fotos compactas quedan dentro de su columna y no se superponen al texto. La instancia temporal de revisión fue retirada al terminar.

La revisión de navegador usó matching por datos declarados. No mide la calidad de identificación por fotos ni confirma entrega de correo real: IA y correo estaban desactivados en esa instancia temporal. El rediseño conserva esos servicios y sus estados de procesamiento.

### Revisión de Apoyanos del 10 de octubre de 2026

TypeScript terminó sin errores y la revisión visual de la página local mostró los cuatro niveles en UYU, la frecuencia, el campo de otro monto, el resumen y el botón de pagos deshabilitado. Se guardó una captura de la página. No se ejecutaron pruebas de flujos ni se enviaron pagos, correos o reportes; esta entrega agrega contenido y selección local al frontend.

### Revisión de reseñas del 10 de octubre de 2026

TypeScript y la sintaxis Python terminaron sin errores. La API inició con la migración `0014_case_reviews` aplicada y la consulta pública devolvió cero reseñas. La portada local se revisó en lectura y se guardó una captura: no muestra la sección de reseñas ni un espacio reservado. No se ejecutaron pruebas automatizadas ni se publicaron reseñas de muestra, se cerraron avisos o se enviaron correos para esta revisión. Los flujos autenticados de escritura quedan implementados sin haber modificado datos de usuarios durante la revisión.
