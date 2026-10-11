# Cómo funciona: recorrido interactivo

## Layout Structure

`HomeHowItWorks` conserva el contenedor de 1280 px, los 24 px laterales y la altura mínima de 72 vh del bloque del inicio. Cuatro pestañas ocupan una fila en escritorio. El panel divide explicación y ejemplo en dos columnas con altura mínima de 470 px. A 640 px o menos, las pestañas usan dos columnas, el panel una y el alto crece con el contenido.

## Section Order

La sección mantiene su lugar después de la portada y antes de los animales perdidos. Presenta título, introducción e invitación a explorar, cuatro pasos seleccionables, explicación y escena del paso activo, y controles Anterior/Siguiente con contador. El último paso permite volver al principio. Las escenas se identifican como ejemplos ilustrativos.

## Navigation

El ancla `#como-funciona` se conserva para el encabezado y el footer. La selección usa `tablist`, `tab`, `tabpanel`, identificadores estables y un único tabulador activo. Flechas izquierda/derecha, Home y End cambian de paso y enfocan su control; clic y toque también seleccionan. Los paneles inactivos permanecen en el DOM con `hidden`. Un estado accesible anuncia el paso. No hay reproducción automática ni cambios de foco al usar los botones Anterior/Siguiente.

## Typography

Se mantiene Arial. El título usa 28–36 px; los títulos de panel, 25–32 px y 26 px en móvil. El texto explicativo usa 16 px, reducido a 15 px en móvil, con interlineado 1,75. Las ayudas usan 13 px. Las pestañas tienen título de 14 px, subtítulo de 12 px y número de 12 px; en móvil el título usa 13 px y se omiten subtítulo y número auxiliares.

## Color System

La publicación utiliza coral y rosa suave; ubicación y comparación, azul y azul suave; reencuentro, verde y verde suave. Todos provienen de los tokens existentes. El texto conserva azul oscuro y gris azulado; las superficies son blancas. La selección combina borde, fondo, icono y atributos accesibles. No se agregan colores a los estados reales de avisos o notificaciones.

## Spacing and Layout Rhythm

La sección tiene 64 px arriba y 72 px abajo. Las pestañas se separan por 16 px y el panel comienza 24 px después. El panel tiene padding de 36 px y gap de 40 px, reducidos a 28 y 24 a 950 px o menos. La escena tiene padding de 24 px y altura mínima de 340 px. En móvil se usan 48 px verticales para la sección, padding de 24 × 20 px para el panel y 20 × 16 px para la escena. El contador pasa a una fila sobre los controles para evitar desbordamiento.

## Image Treatment

Las escenas reutilizan la imagen generada `dog-hero-generated.jpg`, identificada como ilustrativa, con recortes dentro de miniaturas de 112 px y de 80 px para la alerta. En móvil las principales bajan a 90 px. El mapa es un SVG de calles y espacios verdes ficticios, con tres puntos elegibles; no utiliza un proveedor ni solicita la ubicación del dispositivo. Huella, cámara, pin, campana y corazón pertenecen al sistema de iconos existente.

## Cards and Content Blocks

Un marco blanco con radio de 22 px reúne el recorrido. La escena tiene radio de 18 px y fondo suave según el paso. El aviso de ejemplo rota un grado para darle un gesto lúdico; las tarjetas interiores tienen radios de 16 px y sombras suaves. La ayuda funcional usa una superficie suave con escudo. El panel de comparación despliega fotos/rasgos, zona y fecha/hora. El reencuentro muestra una miniatura circular y un corazón que aparece con una animación corta al elegir la recuperación.

## Buttons and CTAs

Los enlaces principales usan el botón coral existente y abren Publicar mascota perdida, Animales perdidos o Mapa según el paso. No se agregan enlaces públicos a Mis avisos ni Notificaciones. Los ejemplos permiten alternar la foto, elegir uno de tres puntos, abrir/cerrar una lista de revisión y comparar Confirmar una pista con Ya la recuperé. Cada control tiene al menos 44 px y un estado accesible (`aria-pressed` o `aria-expanded`). Los estados se conservan localmente al recorrer los pasos.

## Overall Design Feel

El bloque es cercano y juguetón mediante miniaturas, una línea de recorrido, escenas manipulables y transiciones breves, conservando la identidad del sitio. La entrada de escena dura 350 ms y el gesto del corazón 450 ms. La preferencia de movimiento reducido desactiva animaciones y transiciones. El contenido mantiene fotos opcionales, confirmación de correo, avistamientos breves sin cuenta, alertas privadas, comparación humana y la diferencia entre confirmar una pista y cerrar la búsqueda después de la recuperación.

## Implementación y alcance

El componente y su CSS están separados de la página del inicio. La interacción usa estado local de React e iconos existentes, sin dependencias nuevas. Los ejemplos no guardan publicaciones, no consultan coincidencias, no envían correos y no modifican datos de cuentas o reportes. No incluyen puntuaciones de IA ni casos ficticios presentados como reales.

TypeScript finalizó sin errores y la portada local respondió HTTP 200 después de actualizar la web. No se añadieron ni ejecutaron pruebas automatizadas ni se modificaron reportes reales para esta entrega.
