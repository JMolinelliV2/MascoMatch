# Mapa dentro del formulario y perros perdidos

Entrega del 7 de octubre de 2026.

## Cambios

- **Ver en mapa** abre una sección de 300 px en el mismo paso del formulario. Cierra con **Ocultar mapa**.
- El pin se puede arrastrar, mover tocando el mapa o ajustar con las flechas del teclado. Funciona con mouse y pantalla táctil.
- El punto nuevo se guarda al moverlo, se consulta una dirección legible y se descartan dirección y precisión GPS anteriores. Las respuestas de consultas anteriores se cancelan para evitar que cambien el punto nuevo.
- **Perros perdidos**, desde la portada y la navegación, muestra avisos activos de perros con foto opcional, nombre, características, descripción, fecha y localidad.
- Permite buscar por nombre, zona o descripción, navegar páginas de 24 avisos y abrir una ficha individual.
- Los avisos anteriores conservan su localidad mediante la línea `Zona:` que ya guardaba el formulario.

## Archivos

- `apps/web/app/location-map.tsx`, `location-picker.tsx`, `layout.tsx`, `globals.css` y `lib/places.ts`: mapa y selección del punto.
- `apps/web/app/perdidos/`, `lib/lost-dogs.ts`, `app/page.tsx` y `app/site-header.tsx`: listado, ficha, fotos y accesos.
- `apps/web/app/report-form.tsx`: localidad estructurada y acceso al listado tras publicar.
- `apps/api/app/routers/public_lost_dogs.py`, `main.py`, `models.py` y `schemas.py`: rutas públicas y campos permitidos.
- `apps/api/migrations/versions/0003_public_lost_dogs.py`: nueva localidad pública; la migración inicial fija el esquema original de `lost_cases` para que una base nueva también migre correctamente.
- `apps/api/tests/test_public_lost_dogs.py`, `test_analysis_migrations.py` y `apps/web/tests/lost-dogs.test.mjs`: cobertura nueva.
- `apps/web/package.json` y `package-lock.json`: Leaflet 1.9.4 y sus tipos. Sin variables de entorno nuevas.

## Datos públicos

La respuesta pública tiene una lista explícita de campos. No incluye cuenta, contacto, microchip, precisión GPS, coordenadas ni claves de almacenamiento. Las fotos se leen del bucket privado, se limpian y se sirven como JPEG de hasta 1024 px. Se prioriza la foto del aviso y, si no existe, una foto de la mascota.

El listado, la ficha y la foto verifican que el perro tenga un aviso `ACTIVE`. Cuando cambia a `FOUND`, `CLOSED` o `CANCELLED`, o se elimina, dejan de servirlo. Las respuestas no se almacenan en caché. Los datos ya vistos o guardados por un visitante no pueden revocarse.

## Ejecución

```powershell
docker compose restart api web
```

La API aplica `0003_public_lost_dogs` al iniciar. La web instala la biblioteca nueva. En una instalación desde cero: `docker compose --profile ai-local up --build -d`.

Abrir `http://localhost:3000/perdidos`, o seleccionar una ubicación en un formulario y tocar **Ver en mapa**.

## Comprobaciones

- API en Windows: **60 passed, 1 skipped**. La integración optativa de IA local no se volvió a ejecutar en esta entrega.
- API en el contenedor Python: **60 passed, 1 skipped**.
- Frontend: **12 pruebas aprobadas**, TypeScript sin errores y compilación de producción correcta.
- PostgreSQL real: migración `0003_public_lost_dogs (head)` aplicada y API saludable.
- Navegador: aviso existente de Kobe, foto privada servida, búsqueda por nombre, ficha individual, mapa abierto en el formulario y movimiento del pin con teclado y arrastre.
- Pantalla de celular: listado en una columna y navegación sin desbordamiento.

## Límites

El mapa y la búsqueda de direcciones requieren Internet. Las teselas de OpenStreetMap y el geocodificador público no tienen disponibilidad garantizada. Una búsqueda de dirección que falla no deshace el punto elegido en el mapa.

Esta entrega agrega consulta pública de perros perdidos. El contacto privado entre personas, el panel de administración de avisos, los embeddings, el matching y las alertas siguen pendientes.

Referencias: [Leaflet](https://leafletjs.com/) y [política de teselas de OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/).
