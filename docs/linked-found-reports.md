# Mascota bajo cuidado, reportada desde un aviso

El botón «La tengo conmigo» de un aviso abre `/encontre?aviso=…`. Este recorrido puede completarse sin cuenta y es diferente de un avistamiento o del formulario general de mascotas encontradas.

Se requieren una descripción de la mascota, entre una y cinco fotos, el nombre de la persona y un teléfono válido con código de país. Se pueden sumar raza, colores, sexo, tamaño, collar y prendas. No se solicitan ubicación ni fecha de hallazgo: se registra la fecha de envío y no se evalúa la compatibilidad por distancia o fecha.

El reporte crea una alerta para el dueño del aviso seleccionado, independientemente del análisis de IA. Tanto en las notificaciones como en las coincidencias de Mis avisos se muestran las fotos, la descripción y las características declaradas. La alerta por correo dirige a la revisión privada; no contiene el nombre ni el teléfono del informante.

«Podría ser» conserva la revisión pendiente y no habilita el contacto. «Es mi mascota, ver contacto» registra `RESOLVED` sin marcar el aviso como recuperado y permite consultar `GET /matches/{id}/reporter-contact`. Esta ruta exige sesión del dueño, coincidencia confirmada, reporte vinculado y visible, y devuelve `Cache-Control: private, no-store`. Una cuenta diferente recibe 404 y el dueño sin confirmar recibe 403. «Ya la recuperé» sigue siendo una acción separada que cierra la búsqueda.

El nombre y teléfono se guardan en `found_report_contacts` (migración `0033_found_report_contacts`), separados de las respuestas públicas y de los datos enviados a IA. No se agregan al estado público del envío, ni a los resultados de búsqueda, mapas, candidatos o notificaciones serializadas. El contacto no se revela si el dueño descarta el reporte o este deja de estar visible. Se elimina junto al reporte; al eliminar la cuenta del informante también se elimina el contacto que haya dejado, conservando el reporte anónimo.

Los reportes históricos sin contacto siguen disponibles para revisión y muestran que no hay datos de contacto disponibles. Los avistamientos breves mantienen su ubicación y fecha obligatorias, con fotos opcionales.
