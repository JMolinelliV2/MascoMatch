# Diseño del dashboard y ajustes de páginas

## Layout Structure

Las páginas públicas usan el ancho máximo de 1280 px definido en `--site-width`, igual que el inicio. El mapa, las notificaciones, el detalle de avisos y los términos comparten ese contenedor. Los formularios de acceso y contacto mantienen una columna interior de 592 px centrada para conservar su lectura y disposición. Los márgenes laterales son de 24 px en escritorio y 20 px en móvil.

El dashboard autenticado ocupa todo el ancho disponible, sin límite máximo en el contenedor exterior ni en el contenido. Tiene una barra lateral de 242 px y un área de contenido flexible con márgenes interiores. La barra baja a 216 px en pantallas intermedias y se convierte en un menú desplegable por debajo de 1000 px. La cuadrícula de gráficos usa tres columnas; el gráfico de evolución ocupa dos. En pantallas intermedias pasa a dos columnas y en móvil, a una.

## Section Order

Barra superior con sección actual, acceso privado, selector de tema y enlace al sitio; encabezado de la sección; selector temporal compacto; cuatro indicadores principales; evolución de registros y publicaciones; distribución de trabajos; tipos de publicaciones; envíos por tipo; estado de las cuentas; métricas secundarias; cola de correos; fecha de actualización y alcance del historial.

Las listas conservan filtros, resumen de estados, registros, acciones de moderación y paginación. Los formularios Encontré y Avistamiento muestran una explicación breve antes de sus pasos, también en el avistamiento vinculado a un aviso. Se retiró la frase introductoria solicitada de las reseñas; la sección sigue apareciendo únicamente cuando hay reseñas visibles.

## Navigation

La navegación lateral agrupa Plataforma, Inteligencia, Comunicación y Control. Resumen, Usuarios, Publicaciones, Trabajos, Coincidencias, Correos, Contactos, Denuncias y correcciones y Auditoría tienen accesos directos. La selección activa muestra color e icono. En móvil se cierra al elegir una sección, al pulsar fuera o con Escape.

El período se conserva al cambiar entre operación, coincidencias y denuncias. Búsqueda, estado y paginación se reinician al cambiar de lista. El perfil enlaza a Mi cuenta y conserva Cerrar sesión. Los permisos administrativos del servidor se mantienen; no se modifica la asignación de cuentas.

## Typography

Se usa la tipografía del sitio. Los títulos principales tienen 25–32 px; indicadores, 32–44 px; encabezados de tarjetas, 14–16 px. Etiquetas y leyendas compactas tienen 10–12 px. Las cifras usan números tabulares. Los textos largos se ajustan al ancho de las tarjetas.

## Color System

El tema inicial es azul marino oscuro, con superficies en azul profundo y texto claro. Coral conserva la identidad de MascoMatch; turquesa, azul y violeta distinguen los gráficos e indicadores. Los cuatro indicadores destacados usan gradientes suaves. El tema claro tiene superficies blancas, bordes sutiles y los mismos colores de datos. La preferencia se guarda localmente y se limita al dashboard.

Los estados mantienen sus etiquetas además del color: verde para completado/habilitado, coral para fallo/bloqueo y azul para pendientes. El resto del sitio conserva su tema actual.

## Spacing and Layout Rhythm

Contenido con 24–30 px interiores; indicadores con 20 px; gráficos con 22–26 px; separación de tarjetas de 16–22 px. Los filtros temporales están cerrados inicialmente y se abren al seleccionar el período. El resumen elegido queda visible y permite revisar los extremos completos, con precisión de minuto en Uruguay.

## Image Treatment

Se utilizan iconos SVG del sistema existente y gráficos SVG nativos. No se agregan fotografías decorativas, imágenes remotas ni servicios de gráficos. Las fotos de denuncias y avisos conservan sus flujos actuales.

## Cards and Content Blocks

Tarjetas con radios de 12–16 px, bordes de bajo contraste y sombra ligera. Los gráficos de anillo muestran el total y una leyenda con cantidades; al enfocar una categoría se destaca su segmento. La línea temporal permite consultar fechas con el puntero y las flechas del teclado, y tiene una tabla expandible con los valores. Los gráficos sin datos muestran un estado vacío explícito.

Las métricas secundarias conservan toda la información del panel anterior, con explicaciones junto a las cifras. Los mensajes de contacto conservan sus saltos de línea; las referencias técnicas siguen en detalles expandibles.

## Buttons and CTAs

Actualizar, consultar la cola y buscar mantienen botones secundarios. El selector de tema alterna claro/oscuro. Bloquear y restaurar conservan sus confirmaciones y motivos; no se ejecutaron acciones reales de moderación para preparar este diseño. Los formularios Encontré y Avistamiento ofrecen un enlace al otro recorrido cuando corresponde.

## Overall Design Feel

Dashboard inspirado en las referencias del usuario: navegación lateral, contraste, cifras destacadas y visualizaciones agrupadas. Conserva el tono y el coral de MascoMatch y ofrece un modo claro. Las páginas públicas ganan espacio sin alterar campos, reglas de publicación, autenticación, mapas o envíos.

### Datos de los gráficos

La API administrativa agrega datos sin información personal al resumen existente. La evolución cuenta nuevas cuentas y publicaciones por su fecha de creación, agrupando días, semanas, meses o años según la amplitud del rango. Se utiliza la zona America/Montevideo. La serie empieza en el primer registro conservado dentro del período y termina en el extremo elegido o en la fecha actual; no se inventan registros anteriores ni fechas de actividad.

El estado de trabajos usa los trabajos creados en el período y sus estados actuales; tipos de publicaciones incluyen registros conservados, también cerrados u ocultos. Correos por tipo incluye únicamente mensajes con estado SENT del historial real de intentos. El estado de las cuentas distingue habilitadas, bloqueadas y confirmación de correo, sin sumar categorías superpuestas. No se incorporan porcentajes de crecimiento ficticios ni datos de ejemplo a la base.

El resumen muestra Mascotas recuperadas junto al gráfico de publicaciones y entre las métricas de operación. Cuenta avisos creados en el período con estado actual FOUND. El gráfico identifica por separado los reportes publicados desde Encontré una mascota; la recuperación de un aviso existente no crea una nueva publicación ni suma otra categoría al anillo.

### Revisión de la entrega

Se abrió el panel con la sesión administradora y los datos existentes. El resumen y los gráficos cargaron correctamente; se revisaron los temas claro y oscuro, el selector temporal y la navegación adaptable. El período de 30 días se mantuvo al abrir Coincidencias; luego se restauró Todo el período. El menú se cerró al elegir una sección y las recomendaciones existentes conservaron sus estados.

Se revisaron Encontré, Avistamiento y Mapa en el navegador: las explicaciones aparecieron antes de los formularios y los contenedores compartieron el ancho máximo de 1280 px, sin desbordamiento horizontal en la vista revisada. TypeScript y la sintaxis e importación de la API finalizaron sin errores. No se añadieron ni ejecutaron pruebas automatizadas, enviaron formularios o correos, ni aplicaron acciones de moderación durante esta entrega.
