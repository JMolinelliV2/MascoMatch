# Rediseño de MascoMatch

Las cuatro referencias visuales se adaptan al flujo existente. Se conserva la marca MascoMatch, los tres pasos de los formularios generales y el avistamiento breve desde una ficha. Se mantienen las rutas, los campos, las validaciones y los contratos de la API.

## Layout Structure

Contenedor de 1280 px con márgenes automáticos y 24 px laterales. Portada con texto y foto en dos columnas. Formularios con una columna principal flexible y ayuda lateral de 320 px; bajo 950 px pasan a una columna. Desde 360 px los controles se apilan, el stepper muestra la etapa activa y las fotos se pueden recorrer horizontalmente.

## Section Order

Portada: navegación, presentación y acciones para los tres tipos de reporte, explicación breve, avisos activos reales, acceso al mapa y pie con atribución de la fotografía. Formularios: título, tres etapas, campos del paso actual, validación, acciones y ayuda. Mis avisos: sesión, dos cantidades derivadas de los datos, casos con controles, reportes enviados y acceso a notificaciones.

## Navigation

Logo a la izquierda; Inicio, Perdí una mascota, Vi una mascota y Mis avisos en el centro; notificaciones y cuenta a la derecha. Explorar conserva Animales perdidos, Mapa, Encontré una mascota y Cómo funciona. La ruta activa usa subrayado coral y `aria-current`. En pantallas pequeñas hay un menú nativo desplegable y enlaces de cuenta y notificaciones con nombres accesibles.

## Typography

Se conserva Arial, la fuente existente, sin añadir descargas externas. Títulos de página de 32–46 px y peso 800; portada de hasta 58 px; secciones de 22–26 px; tarjetas de 18–22 px; texto de 14–16 px y ayudas de 12–13 px. El contenido largo permite salto de línea.

## Color System

Variables semánticas en `globals.css` y colores equivalentes en el tema Tailwind. Fondo cálido, superficies blancas y texto navy. Coral para acciones principales; azul para información, ubicación y foco; verde para encontrado o compatibilidad alta; amarillo para revisión y advertencias. El coral se oscurece respecto de la referencia para mejorar el contraste del texto blanco. Los estados también llevan texto y no dependen solo del color.

## Spacing and Layout Rhythm

Separaciones de 8, 12, 16, 20, 24, 28 y 32 px. Tarjetas con 24–28 px de padding en escritorio y 16–20 px en móvil. Campos de al menos 48 px y acciones táctiles de al menos 44 px. Ayudas y revisión conservan una jerarquía separada de los campos.

## Image Treatment

La fotografía existente de portada conserva su atribución. Los avisos muestran únicamente fotos reales de la API, con un estado de ausencia cuando no hay foto. Miniaturas cuadradas y fotos de detalle de 4:3. El cargador compartido conserva una foto opcional para reportes generales y hasta cuatro para avistamientos vinculados, con JPEG, PNG y WebP de hasta 10 MB. Incluye selección, arrastre, miniaturas, eliminación y errores; no agrega campos al payload.

## Cards and Content Blocks

Tarjetas blancas, bordes discretos, radios de 12–16 px y sombra mínima. Componentes compartidos para stepper, fotos, iconos, tarjetas de animales y compatibilidad. El panel muestra las cantidades disponibles en sus datos; no se inventan nuevos avistamientos, compartidos, historias o recorridos. La foto de un aviso activo respeta el endpoint público y sus restricciones.

## Buttons and CTAs

Acción principal coral, secundaria blanca con borde y terciaria azul con texto. Radios de 10–12 px. En móvil las acciones principales de publicación ocupan el ancho disponible. Todos los controles de cerrar, quitar foto o navegar tienen texto o nombre accesible. Se mantiene el bloqueo de controles durante las operaciones y el feedback de guardado, error y éxito.

## Overall Design Feel

Herramienta clara y cercana, con fotografías como principal elemento emocional. No se agregan ilustraciones decorativas, métricas ficticias ni mensajes de identidad confirmada a partir de una puntuación. La compatibilidad se muestra con contexto y conserva la revisión humana.

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
