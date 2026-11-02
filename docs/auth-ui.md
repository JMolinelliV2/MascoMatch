# Ingreso y registro

## Layout Structure

`AuthLayout` se comparte entre `/login` y `/crear-cuenta`. La página conserva el ancho general de 1280 px. Una tarjeta distribuye formulario e ilustración en columnas de proporción 1.08:1. Hasta 760 px se apilan: ilustración arriba y formulario debajo, con una curva blanca que se superpone al panel de imagen.

## Section Order

Se conserva el encabezado general. Dentro de la tarjeta aparecen el selector de ingreso/registro, el título, los campos, la acción principal y el acceso alternativo. En escritorio, la ilustración acompaña a la derecha; en celular se presenta primero. El footer general continúa al final.

## Navigation

El selector superior usa enlaces reales y `aria-current`, sin simular pestañas con un comportamiento de teclado distinto. Se conservan los enlaces de recuperación, registro, ingreso, términos y confirmación de correo. El menú global mantiene sus opciones existentes.

## Typography

Se utiliza Arial/Helvetica, igual que el resto del sitio. Títulos de 28–36 px, etiquetas de 14 px y entradas de 16 px. Las ayudas usan 12 px; la jerarquía conserva las etiquetas visibles incluso cuando se completa el campo.

## Color System

Se mantienen azul oscuro `--text-primary`, coral `--primary`, blanco y fondo crema. Campos y selector tienen un fondo gris azulado suave. Los enlaces de recuperación y el foco usan el azul del sistema.

## Spacing and Layout Rhythm

El contenido tiene hasta 440 px de ancho dentro de su columna. Los campos se separan 20 px en ingreso y 16 px en registro; las entradas miden al menos 52 px de alto. El padding se reduce en celulares, sin imponer un alto fijo al formulario ni bloquear su desplazamiento.

## Image Treatment

Se utilizan dos ilustraciones locales originales: `auth-login-illustration.webp` para ingreso y `auth-register-illustration.webp` para registro. Las escenas muestran personas en casa con un perro y un gato. Los archivos WebP conservan transparencia y se muestran completos mediante `object-fit: contain`. El panel tiene fondo azul suave en ingreso y coral suave en registro. El texto se coloca debajo de la escena en azul oscuro, sin superposición ni degradado. En celular se oculta ese texto largo y el panel muestra la ilustración completa con una insignia pequeña. Todo el panel es decorativo para tecnologías de asistencia. La generación se documenta en [auth-illustrations.md](./auth-illustrations.md).

## Cards and Content Blocks

La tarjeta combina un borde suave, radio de 28 px y sombra tenue. Los campos tienen radio de 13 px. Las pantallas de carga, errores y confirmación conservan su comportamiento y se integran en la misma columna.

## Buttons and CTAs

Ingresar y Crear cuenta conservan el botón coral del sitio, ocupan el ancho del formulario y tienen una flecha. El control de visibilidad de contraseña tiene un objetivo táctil de 44 px, nombre accesible y estado presionado; no envía el formulario. Respeta el estado deshabilitado del fieldset durante el envío.

## Overall Design Feel

El diseño combina las referencias de formularios con escenas ilustradas adaptadas a la identidad de MascoMatch. No incorpora redes sociales, recordar sesión ni nuevas opciones de cuenta. Se conservan nombres de campos, validaciones, envío, analítica de registro, redirecciones de sesiones existentes y verificación de correo.

## Revisión

Se comprobaron TypeScript, sintaxis CSS y los cambios de formato. La revisión visual utilizó las páginas reales en 320, 390, 768 y 1280 px, sin desbordes horizontales. Se verificaron los controles de visibilidad, la navegación entre formularios y los atributos de nombre, longitud, autocompletado y obligatoriedad de los campos. No se iniciaron sesiones ni crearon cuentas durante la revisión.
