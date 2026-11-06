# Frontend: componentes y criterios de mantenimiento

Revisado el **5 de noviembre de 2026**. El comportamiento completo está en [Flujos del sistema](FLUJOS_DEL_SISTEMA.md); esta guía ubica las piezas compartidas para modificarlas sin romper los recorridos.

## Estructura y estilos

La web utiliza Next.js App Router, React y TypeScript. [globals.css](../apps/web/app/globals.css) concentra los tokens de color, ancho, espacios, componentes y reglas adaptables. Las páginas públicas comparten `--site-width`, actualmente 1280 px, con columnas interiores más estrechas donde conviene para leer o completar formularios. El dashboard autenticado ocupa todo el ancho disponible.

La identidad utiliza coral, azul oscuro, fondos crema y superficies suaves azules o verdes. Los estados se explican también con texto; el color no es su único indicador. Los iconos pertenecen al sistema del sitio.

| Área | Fuente principal |
| --- | --- |
| Navegación y sesión | [site-header.tsx](../apps/web/app/site-header.tsx) |
| Inicio y sus secciones | [page.tsx](../apps/web/app/page.tsx) y sus componentes en `app/` |
| Publicación general | [report-form.tsx](../apps/web/app/report-form.tsx) |
| Reportes dirigidos a un aviso | [linked-sighting-form.tsx](../apps/web/app/linked-sighting-form.tsx) |
| Campos de características | [report-trait-fields.tsx](../apps/web/app/ui/report-trait-fields.tsx) |
| Catálogo y filtros | [lost-dogs.tsx](../apps/web/app/perdidos/lost-dogs.tsx) |
| Datos privados y edición | [Mis avisos](../apps/web/app/mis-avisos/my-reports.tsx) |

Publicar y Explorar agrupan recorridos. La cuenta tiene su propio desplegable; Notificaciones y Mis avisos dependen de la sesión, y Administración depende además del permiso devuelto por el servidor. Clic fuera y Escape cierran los menús. Ocultar un enlace no sustituye una comprobación de acceso en la API.

## Formularios y sugerencias

Los formularios generales conservan tres pasos. Los vinculados no se deben convertir en una copia del formulario general: «La vi» necesita lugar y fecha, mientras que «La tengo conmigo» solicita fotos, descripción y contacto privado, sin ubicación ni fecha de hallazgo.

Los campos de descripción representan lo escrito por la persona. [report_text.py](../apps/api/app/report_text.py) distingue texto de usuario, contexto del sistema y registros antiguos; una edición no debe volver a insertar líneas de características o resultados de IA.

[SuggestionField](../apps/web/app/ui/suggestion-field.tsx) es el control editable de sugerencias para razas y colores. Mantiene el ancho del campo, permite escribir un valor nuevo y admite teclado, Escape, clic fuera y composición de texto. [suggestions.ts](../apps/web/lib/suggestions.ts) normaliza acentos y completa el último color de una lista separada por comas. No sustituirlo por `datalist`, cuyo panel depende del navegador y no conserva el estilo del sitio.

El [catálogo de razas](../apps/web/lib/breed-catalog.ts) es la fuente única de las opciones importadas: 214 nombres de perro y 53 de gato, recopilados el 2 de noviembre de 2026 de los directorios de [perros de Purina](https://www.purina.es/encuentra-mascota/razas-de-perro) y [gatos de Purina](https://www.purina.es/encuentra-mascota/razas-de-gato). La recopilación recorrió 18 y 5 páginas respectivamente. Se incorporaron nombres, sin imágenes ni descripciones. Los controles conservan Mestizo, las opciones anteriores y el ingreso libre; no se duplica la lista completa en Markdown.

## Ubicación y mapas

[LocationPicker](../apps/web/app/location-picker.tsx) y [LocationMap](../apps/web/app/location-map.tsx) se comparten entre creación y edición. Un lugar válido muestra automáticamente el mapa dentro de la página. El pin admite arrastre, toque y teclado; escribir otra dirección sin seleccionar un resultado no debe dejar guardadas coordenadas anteriores como si correspondieran al texto nuevo.

La búsqueda usa el contrato Photon a través de `/api/places`. El país de referencia puede provenir del dispositivo; sin esa referencia se utiliza `NEXT_PUBLIC_SEARCH_COUNTRY`, por defecto `UY`. Se filtra por país y se priorizan coincidencias exactas y cercanía según los datos disponibles. El origen de la persona es independiente del lugar del reporte.

Leaflet muestra el mapa y la cartografía configurada. `/mapa` presenta pérdidas en rojo y avistamientos en azul; no ofrece la capa de encontrados. Los datos públicos son aproximados. Las fotos de un avistamiento son las de ese reporte: nunca se presenta la imagen del aviso perdido como evidencia aportada por otra persona.

La configuración del proveedor y sus límites se revisan en la [puesta en producción](puesta-en-produccion-paso-a-paso.md#9-definir-la-búsqueda-de-direcciones-y-los-mapas).

## Fotos y acceso a imágenes

Los álbumes admiten hasta cinco JPEG, PNG o WebP, de hasta **10 MiB por archivo**. La carga por lote, el límite total y la portada se comprueban en el servidor; elegir otra miniatura no vuelve a analizar las fotos. Las fotos heredadas del perfil de la mascota cuentan en el álbum del aviso.

El formulario conserva la selección al agregar archivos y permite elegir la principal. La ficha muestra esa imagen grande y las otras como miniaturas; las tarjetas del catálogo permiten recorrer las fotos. El visor ampliado se monta fuera del mapa o tarjeta, conserva proporción, controla foco, cierra con Escape y devuelve el foco al control de apertura.

Las rutas públicas y privadas comprueban visibilidad, pertenencia y sesión según el caso. No se exponen claves del bucket ni URLs S3 firmadas como sustituto de esos controles. Las imágenes procesadas no conservan EXIF. El avatar utiliza su propio objeto privado; no se registra como foto de mascota ni genera trabajos de IA.

Los proxies admiten hasta 52 MiB por lote y Caddy limita el cuerpo a 55 MB. Esos valores deben seguir siendo compatibles con las cinco fotos y con la admisión de cargas. Fuentes: [photo_albums.py](../apps/api/app/photo_albums.py), [galerías](../apps/api/app/routers/photo_gallery.py) y [Caddyfile](../infrastructure/production/Caddyfile).

## Acceso, cuenta y reseñas

`AuthLayout` reúne ingreso y registro en una tarjeta con formulario e ilustración. En pantallas pequeñas se apilan y la imagen conserva su proporción. Las etiquetas permanecen visibles; el botón de mostrar contraseña es independiente del envío.

Mi cuenta agrupa contacto, foto ajustable, contraseña, preferencias y eliminación. El encuadre del avatar se exporta a JPEG cuadrado; ajustar una imagen ya guardada no recupera partes descartadas del archivo original. Las reseñas con nombre pueden usar el avatar actual; las anónimas no lo muestran. Sin reseñas elegibles no se renderiza la sección.

## Indicadores de carga

[LoadingState](../apps/web/app/ui/loading-state.tsx) utiliza logo, mensaje y el perro animado local. Se monta mediante portal en el cuerpo del documento y cubre `100dvh`, con respaldo `100vh`, para evitar que una tarjeta limite su tamaño. Mientras está presente se bloquea el scroll del documento. `AccountLoading` reutiliza el mismo indicador.

La variante `compact` muestra un indicador pequeño para mapas, tarjetas y secciones; no bloquea la página ni muestra el perro. El estado se anuncia mediante `role="status"` y `aria-live="polite"`. Con movimiento reducido se usa una imagen quieta y se detienen los indicadores animados. No se agregan esperas artificiales.

## Ilustraciones y animación

Los archivos se sirven desde `apps/web/public/images`. Su procedencia, adaptaciones y licencias se conservan junto a los recursos en el [README de imágenes](../apps/web/public/images/README.md).

- El hero utiliza una imagen generada para MascoMatch.
- Ingreso y registro utilizan ilustraciones originales adaptadas a la paleta, sin representar personas usuarias reales.
- Cómo funciona presenta cuatro pasos visibles con ilustraciones, números y texto unificado. Conserva sus anclas; no incluye CTA ni rebote de imágenes.
- La carga utiliza las doce poses aportadas por el usuario, en WebP de 500 × 500, con ciclo de 1,26 segundos y una alternativa quieta.

## Correos y páginas legales

[mail_templates.py](../apps/api/app/mail_templates.py) reúne el marco HTML del correo, logo por CID, alternativa de texto y botones centrados. No depende de fuentes o imágenes externas. Cambiar el diseño no debe alterar destinatarios, enlaces de acceso, reintentos o condiciones de envío; esos contratos están en [operación](production.md#correo-y-contacto) y en los [flujos](FLUJOS_DEL_SISTEMA.md#16-notificaciones-y-correos).

Los textos públicos viven en [Términos](../apps/web/app/terminos/page.tsx) y [Privacidad](../apps/web/app/privacidad/page.tsx). El footer compartido ofrece sus enlaces. La documentación técnica no mantiene otra versión de esas condiciones ni certifica su adecuación jurídica. Los formularios enlazan la información sin perder el contenido que la persona está completando.

## Comprobaciones al modificar la interfaz

Desde `apps/web`, ejecutar `npm test`, `npm run typecheck` y `npm run build` según el cambio. Revisar escritorio y móvil, teclado, campos conservados al volver entre pasos, errores, estados sin datos y movimiento reducido. Las comprobaciones visuales no requieren publicar avisos reales, modificar cuentas o enviar correos externos.
