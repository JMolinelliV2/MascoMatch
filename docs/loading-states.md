# Indicadores de carga

`apps/web/app/ui/loading-state.tsx` reúne el logo de MascoMatch, un perro ilustrado que corre y un mensaje que identifica la carga en curso. La animación usa SVG y CSS locales, sin imágenes externas, consultas adicionales ni temporizadores de JavaScript.

Se utiliza en las transiciones de página, acceso a la cuenta, avisos, reportes vinculados, edición, notificaciones, recuperación y confirmación de correo, mapa y panel administrativo. `AccountLoading` conserva su interfaz y las siluetas de avisos opcionales, usando el mismo indicador. La versión compacta sirve para secciones y miniaturas del mapa.

El componente solo representa el estado existente. No demora respuestas, no altera solicitudes, filtros, permisos ni formularios y desaparece al llegar los datos o mostrarse un error. Los estados de botones y tareas secundarias conservan sus mensajes específicos.

El texto se anuncia con `role="status"`, `aria-live="polite"` y `aria-atomic="true"`. La ilustración y el logo decorativos se excluyen de los anuncios. Con `prefers-reduced-motion: reduce` se detienen el recorrido, las patas, la cola y los puntos; quedan visibles el perro y el mensaje.

Se verificaron la vista de escritorio y una pantalla de 375 px, además de TypeScript y las pruebas web. La página temporal de revisión no forma parte del sitio publicado.
