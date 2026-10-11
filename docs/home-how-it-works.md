# Cómo funciona: recorrido ilustrado

## Layout Structure

El bloque conserva el ancho general de 1280 px del inicio y usa una cabecera centrada de hasta 720 px. El recorrido ocupa hasta 1140 px, con cuatro filas abiertas. Cada fila distribuye ilustración, punto numerado y explicación en tres columnas: `1fr / 144 px / 1fr`, con 20 px entre columnas. Ilustración y texto alternan de lado. La fila mide al menos 380 px y crece al desplegar información.

A 1000 px o menos, el centro baja a 112 px, el espacio entre columnas a 12 px y las ilustraciones a 280 px. A 760 px o menos, una columna lateral de 52 px contiene los números y otra flexible contiene ilustración y texto apilados. El recorrido crece con el contenido y conserva los cuatro pasos visibles.

## Section Order

La sección sigue después de la portada y antes de los animales perdidos. Presenta título, introducción y un enlace al comienzo del recorrido. Los pasos son: publicar el aviso, sumar un avistamiento, revisar pistas y cerrar la búsqueda tras el reencuentro. Una frase breve cierra el bloque. Las ilustraciones son conceptuales y no muestran reportes reales.

## Navigation

Se conserva `#como-funciona` para la navegación del encabezado y el footer. “Seguí el recorrido” apunta a `#how-notice`. Los cuatro pasos forman una lista ordenada. Sus enlaces llevan a las rutas existentes `/perdi`, `/perdidos` y `/mapa`.

Cada paso tiene un desplegable nativo `details/summary` con una aclaración funcional. Admite teclado, anuncia su estado mediante la semántica del navegador y conserva el indicador de foco del sitio. Los números y la línea son decorativos; el texto accesible identifica el número de cada paso. No se muestran enlaces públicos a Mis avisos ni Notificaciones.

## Typography

Se mantiene Arial. El título principal usa 30–42 px, peso 800 e interlineado 1,18; en móvil, 32 px. La introducción usa 18 px y baja a 16 px en móvil. Los títulos de paso usan 26–34 px, peso 750, interlineado 1,2 y balance de líneas; a 1000 px o menos usan 28 px, y a 760 px o menos, 26 px. Los párrafos usan 16 px e interlineado 1,75, reducidos a 15 px y 1,7 en móvil. Las aclaraciones usan 13–14 px; los números, 23 px en escritorio, 21 px en tablet y 18 px en móvil.

## Color System

La superficie abierta utiliza el fondo crema del sitio. El texto conserva azul oscuro y gris azulado. Publicación usa coral; comunidad y revisión, azul; reencuentro, verde. Cada paso reutiliza los tokens de acento y fondo suave existentes. La línea base usa `#c7d8e4` y su tramo recorrido usa coral. Los puntos visitados combinan borde, fondo suave y número con el acento de su paso.

Las ilustraciones comparten azul oscuro, coral, celeste suave, verde apagado y pequeños detalles mostaza. Los estados decorativos del recorrido no representan el estado de una publicación ni una identidad confirmada.

## Spacing and Layout Rhythm

La sección tiene 88 px superiores, 76 px inferiores y 24 px laterales. La cabecera se separa 52 px del recorrido; las filas, 32 px entre sí. El título de cada paso sigue a una etiqueta de 12 px, con 12 px de separación. El párrafo empieza 18 px después del título. Las aclaraciones y enlaces tienen áreas de interacción de al menos 44 y 48 px respectivamente.

En tablet el padding superior baja a 64 px. En móvil la sección usa 56 px verticales y 20 px laterales; la cabecera se separa 32 px del recorrido. Las filas tienen 44 px de separación; las dos columnas, 18 px, y la ilustración se separa 18 px del texto. La frase final se separa 48 px del recorrido en escritorio y 36 px en móvil.

## Image Treatment

Se generaron cuatro ilustraciones originales con la herramienta integrada imagegen el 11 de octubre de 2026. Representan publicación desde el teléfono, una persona fotografiando un avistamiento, revisión humana de fotografías y un reencuentro con perro y gato. Toman la composición abierta y el tono editorial de las referencias del usuario.

Los archivos son WebP de 1254 × 1254 px con transparencia, sin recorte de la composición y optimizados con calidad 88. Se sirven desde `public/images` con Next Image, `sizes` adaptativo y carga diferida. Su ancho máximo visible es 360 px en escritorio, 280 px en tablet y 300 px en móvil. El texto contiguo explica completamente cada paso; las imágenes decorativas tienen `alt` vacío para evitar repetición. Los prompts y archivos se documentan en `apps/web/public/images/README.md`.

## Cards and Content Blocks

Las cuatro escenas se presentan sobre el fondo abierto de la página. Un camino curvo conecta círculos numerados de 72 px; en tablet son de 64 px y en móvil, 48 px. El paso actual agrega un halo de 8 px. Cada ilustración tiene un pequeño sello circular con un icono del sistema existente. Las aclaraciones abiertas añaden una línea lateral del color del paso y texto de 14 px.

El camino usa un SVG construido a partir de la posición real de los números. Se recalcula cuando cambia el ancho, las fuentes o el alto de una fila al abrir sus detalles. Si JavaScript o alguna API de observación no está disponible, todo el contenido sigue visible; una línea vertical sirve de base antes de calcular la curva.

## Buttons and CTAs

El primer paso usa el botón coral existente, de al menos 48 px, para publicar una mascota perdida. En móvil ocupa todo el ancho de su columna. Los siguientes pasos usan enlaces con flecha y el color de su etapa: ver animales perdidos, explorar el mapa y seguir ayudando. La flecha se desplaza 4 px al pasar el puntero; los enlaces de texto también se subrayan.

Los desplegables informan sobre correo confirmado, fotos opcionales, avistamientos generales, recepción de pistas y confirmación frente a recuperación. Sus flechas cambian de orientación con el estado abierto. El enlace superior desplaza al comienzo del recorrido.

## Overall Design Feel

La sección utiliza una composición editorial con aire, escenas de personas y mascotas, texto alternado y un camino numerado. Retoma los ejemplos aportados por el usuario y mantiene la identidad de MascoMatch. El tono es cálido y lúdico, con títulos directos e información funcional accesible.

El camino se colorea con el avance por la página. IntersectionObserver activa una entrada suave de 600 ms para el texto y 750 ms para la ilustración, una única vez por escena. El contenido permanece visible antes de esas animaciones. El hover mueve la imagen 4 px y rota un grado; la preferencia de movimiento reducido elimina animaciones y transformaciones de hover.

## Implementación y alcance

`HomeHowItWorks` y su CSS conservan su ubicación independiente de la página principal. El recorrido usa APIs nativas, sin nuevas dependencias. Su estado controla únicamente la decoración y el despliegue local de información. Se conserva la publicación con correo confirmado, el avistamiento breve sin cuenta, la recepción de pistas vinculadas, la revisión humana de coincidencias y el cierre del aviso tras recuperar al animal.

TypeScript terminó sin errores. No se añadieron ni ejecutaron pruebas automatizadas para esta modificación.
