# Indicadores de carga

`apps/web/app/ui/loading-state.tsx` reúne el logo de MascoMatch, el perro de pañuelo coral aportado por el usuario el 5 de noviembre de 2026 y un mensaje que identifica la carga en curso. Se conservan las doce poses de `mascomatch_spritesheet_animado.svg`, con un ciclo de 1,26 segundos, convertidas a WebP animado de 500 × 500. El perro corre en el centro y permanece visible durante todo el ciclo. El archivo se sirve desde el sitio y no necesita temporizadores ni librerías de animación.

Se utiliza en las transiciones de página, acceso a la cuenta, avisos, reportes vinculados, edición, notificaciones, recuperación y confirmación de correo. Todo indicador con el perro cubre la ventana completa (`100dvh`, con respaldo `100vh`), centra el contenido y oculta el desplazamiento del documento mientras está presente. Se monta en el cuerpo del documento para que ninguna tarjeta, columna de acceso o contexto de apilamiento limite su tamaño. `AccountLoading` conserva su interfaz usando este mismo indicador, sin una tarjeta ni siluetas adicionales.

Las cargas parciales de mapas, miniaturas, secciones del inicio y pestañas administrativas usan la variante `compact`: un círculo animado y el mensaje de estado, sin el perro ni una pantalla superpuesta. Así no bloquean el resto de la página mientras actualizan una sección.

El componente solo representa el estado existente. No demora respuestas, no altera solicitudes, filtros, permisos ni formularios y desaparece al llegar los datos o mostrarse un error. Los estados de botones y tareas secundarias conservan sus mensajes específicos.

El texto se anuncia con `role="status"`, `aria-live="polite"` y `aria-atomic="true"`. La ilustración y el logo decorativos se excluyen de los anuncios. Con `prefers-reduced-motion: reduce`, `<picture>` selecciona `loading-dog-still.webp` en lugar de la animación; también se detienen los puntos y el indicador compacto. El mensaje se conserva en ambos casos.

Se verificaron la vista de escritorio y una pantalla de 375 px, además de TypeScript y las pruebas web. La página temporal de revisión no forma parte del sitio publicado.
