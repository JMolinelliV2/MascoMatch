# MascoMatch: flujos implementados

**Fecha de revisión: 5 de noviembre de 2026.**

Este documento describe el comportamiento del código actual, sus pantallas, los procesos en segundo plano y las acciones de operación. Que una integración esté implementada no significa que esté habilitada en una instalación: SMTP, los modelos de IA, Mercado Pago y Backblaze requieren su configuración correspondiente. No se presupone que el proyecto ya esté desplegado en un VPS. Las guías técnicas y operativas se organizan en el [índice de documentación](README.md).

## 1. Conceptos y participantes

| Concepto | Qué representa |
| --- | --- |
| Mascota | El perfil con nombre, especie y características. Se admiten perros y gatos. |
| Aviso de pérdida | Una búsqueda abierta por el dueño, asociada a una mascota. |
| Avistamiento | Una persona vio una mascota, pero no la tiene bajo su cuidado. |
| Reporte de mascota encontrada | Una persona indica que la mascota está a salvo bajo su cuidado. No acredita por sí solo que el dueño la haya recuperado. |
| Reporte general | Se publica sin elegir antes un aviso perdido; el sistema busca avisos compatibles. |
| Reporte vinculado | Se envía para un aviso específico mediante «La vi» o «La tengo conmigo». |
| Coincidencia | Una relación entre un aviso perdido y un reporte, que el dueño puede revisar. |
| Recuperación | El dueño confirma que ya volvió a tener a su mascota. Cierra la búsqueda activa. |

Los actores son el visitante sin cuenta, el usuario registrado, el usuario con correo confirmado, el dueño de un aviso, el autor de un reporte y la cuenta administradora. Las comprobaciones de acceso se realizan en el servidor; no dependen solamente de los botones visibles.

### Accesos según la sesión

- Sin cuenta se puede explorar el catálogo y el mapa, abrir avisos, ampliar fotos, enviar contacto o denuncias, consultar Apoyanos y completar los reportes breves vinculados a un aviso.
- Publicar mediante los formularios generales, editar publicaciones y cargar sus fotos requiere una cuenta con correo confirmado.
- Mis avisos y Notificaciones se ofrecen en el menú cuando hay sesión. Mi cuenta agrupa los datos personales, la foto, la contraseña y las preferencias.
- Administración aparece para la cuenta administradora habilitada. Una sesión común no obtiene acceso entrando manualmente en `/admin`.

## 2. Todos los puntos de entrada para publicar

| Recorrido | Pantalla | Desde dónde se llega | Cuenta necesaria para enviar |
| --- | --- | --- | --- |
| Perdí una mascota | `/perdi` | CTA principal del inicio; menú Publicar; footer; botón Publicar un aviso del catálogo; acciones equivalentes de los estados vacíos. | Sí, con correo confirmado. |
| Vi una mascota, sin aviso elegido | `/avistamiento` | CTA del inicio; menú Publicar; footer; cambio desde el formulario general de encontrada. | Sí, con correo confirmado. |
| Encontré una mascota, sin aviso elegido | `/encontre` | CTA del inicio; menú Publicar; footer; cambio desde el formulario general de avistamiento. | Sí, con correo confirmado. |
| La vi, para un aviso particular | `/avistamiento?aviso=ID_INTERNO` | Botón La vi de la ficha de una mascota perdida; cambio desde La tengo conmigo del mismo aviso. | No. |
| La tengo conmigo, para un aviso particular | `/encontre?aviso=ID_INTERNO` | Botón La tengo conmigo de la ficha de una mascota perdida; cambio desde La vi del mismo aviso. | No. |

La ficha del aviso se puede abrir desde las tarjetas del inicio, el catálogo `/perdidos`, el mapa del inicio, los marcadores del mapa completo y las posibles coincidencias mostradas tras un reporte o en Mis avisos. En esos recorridos se abre la ficha y desde allí se elige uno de los dos botones: no todos los mapas o tarjetas tienen un formulario de publicación propio.

Los enlaces con `?aviso=…` usan el identificador interno del aviso. No se debe confundir ese identificador con el código público `MM-000123`. El cambio entre los dos formularios breves conserva el aviso elegido; el cambio entre formularios generales no inventa un vínculo.

Después de publicar un reporte general, Crear otro reporte reinicia ese formulario. Si un aviso vinculado ya no está disponible, la pantalla ofrece publicar un reporte general.

## 3. Publicar una mascota perdida

**Actor:** dueño con cuenta y correo confirmado. **Entrada:** `/perdi`.

1. En Mascota se eligen perro o gato y se completan nombre, descripción y las características conocidas: sexo, tamaño, raza, colores, collar y prendas. No se pregunta cómo se perdió.
2. Se pueden cargar hasta cinco fotos y elegir la principal. En este recorrido las fotos son opcionales.
3. Si se intenta continuar sin fotos, aparece una recomendación para agregarlas. Se puede abrir el selector o continuar sin foto; el aviso no queda bloqueado por esa elección.
4. En Fecha y lugar se indica cuándo se perdió y se selecciona una dirección o la ubicación del dispositivo. La ubicación es obligatoria para un aviso de pérdida.
5. El mapa aparece automáticamente al elegir el lugar. El dueño puede ajustar el punto antes de continuar.
6. En Contacto y revisión se repasan los datos. Si no existe una sesión, el formulario permite ingresar o crear una cuenta. Si falta confirmar el correo, se pide completar esa confirmación antes de publicar.
7. El sistema guarda la mascota y su aviso de pérdida, asigna un código público único y presenta la confirmación con acceso a Mis avisos.
8. La extracción de características y la búsqueda de coincidencias se programan en segundo plano cuando los servicios de IA están habilitados.

Los pasos conservan sus campos mientras se navega entre ellos. Esto no equivale a un borrador permanente recuperable después de cerrar la pestaña. La descripción guardada corresponde a lo escrito por la persona; no se le agregan automáticamente raza, zona o resultados de IA.

**Resultado:** aviso `ACTIVE`, visible en el catálogo y, cuando tiene ubicación, en los mapas públicos. Su código público se conserva al editarlo, cerrarlo o reabrirlo.

### Recordatorio posterior si faltan fotos

- Se programa al crear el aviso; la espera predeterminada es de 30 minutos y es configurable.
- Antes de enviarlo se comprueba que la búsqueda siga activa y visible, que todavía no tenga fotos y que la cuenta esté habilitada y con correo confirmado.
- Si se agregaron fotos, se cerró el aviso o la mascota ya fue recuperada, se cancela el recordatorio.
- Si los correos están desactivados por preferencia del dueño, se omite. Si falta verificar el correo, se posterga la comprobación.
- El correo recomienda varias fotos claras y diferentes ángulos; su botón lleva a la gestión de fotos del aviso en Mis avisos.

## 4. Publicar un avistamiento general

**Situación:** se vio una mascota suelta y no se eligió un aviso perdido antes de comenzar. **Entrada:** `/avistamiento`, sin `aviso`.

1. Se completan especie, descripción y las características que se puedan reconocer. Las fotos son opcionales, con un máximo de cinco.
2. Se indica cuándo se la vio. Se puede añadir un lugar; en este formulario general la ubicación es opcional. Si se escribe una dirección, debe elegirse un resultado para guardarla.
3. Se revisa el reporte y se ingresa con una cuenta confirmada, o se crea y confirma una cuenta.
4. Se guarda una observación de tipo `USER_SIGHTING`, asociada a su autor.
5. El sistema la compara con búsquedas activas. La pantalla de resultado y Mis avisos permiten consultar las posibles coincidencias.
6. Cuando existe evidencia suficiente para una alerta automática, el dueño del aviso compatible recibe una notificación y se programa el correo, según sus preferencias.

En la revisión se puede autorizar que el correo de la cuenta se comparta de forma privada con los dueños que reciban una posible coincidencia. La autorización es opcional y se puede modificar al editar el reporte. No publica el correo en el mapa o catálogo.

**Diferencia respecto de un reporte vinculado:** no se notifica a un dueño concreto solo por haber publicado. La comparación general decide qué relaciones resultan suficientemente relevantes. Sin ubicación o sin evidencia suficiente puede no generarse una recomendación automática.

## 5. Publicar una mascota encontrada sin elegir un aviso

**Situación:** la persona tiene a la mascota a salvo, pero aún no encontró su aviso de pérdida. **Entrada:** `/encontre`, sin `aviso`.

El recorrido general usa las mismas tres etapas de datos, fecha/lugar y revisión/cuenta. Permite describir a la mascota, adjuntar hasta cinco fotos, indicar cuándo se la encontró y añadir ubicación opcional. Al enviar exige cuenta con correo confirmado.

Se guarda una observación `FOUND_ANIMAL`. El sistema busca avisos perdidos compatibles y ofrece esas coincidencias al autor en la confirmación del reporte y en Mis avisos. Si se abre un aviso compatible, su ficha permite continuar con las acciones vinculadas.

También permite autorizar el intercambio privado del correo de la cuenta ante una posible coincidencia, igual que el avistamiento general.

Este formulario general no es el formulario breve de «La tengo conmigo». El intercambio de nombre y teléfono condicionado a la confirmación del dueño corresponde al recorrido vinculado descrito en la sección 7.

## 6. «La vi»: avistamiento enviado desde un aviso

**Situación:** se cree haber visto a la mascota de una ficha particular, pero no está bajo el cuidado de quien reporta. **Entrada:** `/avistamiento?aviso=…`.

1. La pantalla carga la foto, el nombre y el código del aviso elegido.
2. Se solicita dónde se la vio: dirección elegida de la búsqueda, GPS o punto ajustado en el mapa. Aquí la ubicación sí es obligatoria.
3. Se mantiene La vi recién o se indica una fecha y hora aproximadas.
4. Se pueden adjuntar hasta cinco fotos y sumar características observadas. No es necesario volver a describir todos los datos del aviso original.
5. Se envía con o sin cuenta. Con sesión, el reporte queda asociado a esa cuenta; sin sesión, queda anónimo.
6. El reporte se guarda vinculado al aviso y llega al dueño aunque la comparación automática esté pendiente, no tenga fotos o detecte incompatibilidades.
7. La confirmación del envío informa el estado real de la revisión. Si sigue pendiente, la pantalla consulta el avance durante un período limitado y permite actualizarlo manualmente después.

El dueño recibe las fotos disponibles, los motivos de comparación y la ubicación precisa de forma privada. El mapa público utiliza una zona aproximada. Los datos del aviso perdido no se copian como si fueran observaciones independientes de quien envía la pista.

Los reportes enviados por el propio dueño para su aviso no le generan una alerta para sí mismo. Si el aviso dejó de estar activo, no se acepta un nuevo reporte vinculado para esa búsqueda.

## 7. «La tengo conmigo»: mascota bajo cuidado, vinculada a un aviso

**Situación:** la persona tiene una mascota que cree que corresponde a un aviso concreto. **Entrada:** `/encontre?aviso=…`.

1. Se carga el aviso seleccionado y se explica que primero se revisará la identidad de la mascota.
2. Se solicita al menos una foto, hasta un máximo de cinco, y una descripción de lo que la persona tiene delante. Se pueden añadir sexo, tamaño, raza, colores, collar y prendas.
3. Se solicitan nombre y teléfono de contacto. El formulario explica que se compartirán con el dueño únicamente después de que confirme la identidad.
4. No se pide lugar ni fecha de hallazgo. Se registra la fecha de envío; el lugar donde se encontró no condiciona este recorrido.
5. Puede enviarse sin cuenta. El sistema guarda los datos de la mascota y almacena el nombre y teléfono en un registro privado separado.
6. Se genera una alerta para el dueño del aviso elegido. No se espera una aprobación del modelo ni se descarta el reporte por distancia o fecha de hallazgo.
7. En Notificaciones o Mis avisos, el dueño ve primero las fotos, la descripción y las características declaradas. Todavía no obtiene el nombre ni el teléfono.
8. «Podría ser, todavía no estoy seguro» mantiene el contacto oculto. «No es mi mascota» descarta el reporte.
9. «Es mi mascota, ver contacto» confirma la identidad y habilita la consulta privada del nombre y teléfono para coordinar la entrega.
10. El aviso continúa activo. Solo «Ya la recuperé» confirma que la mascota volvió con su dueño y retira la búsqueda del catálogo.

El servidor vuelve a verificar la titularidad y la confirmación al consultar el contacto. Una cuenta diferente no puede obtenerlo conociendo el enlace. Los datos no se incluyen en respuestas públicas, mapas, estado público del envío ni correos previos a la confirmación. Los reportes históricos que no tienen ese contacto muestran que no hay datos disponibles.

El contacto declarado en este formulario es independiente de Mi cuenta: cambiar después el nombre o teléfono del perfil no modifica automáticamente lo que se dejó en el reporte. Actualmente el editor del reporte permite cambiar los datos de la mascota y sus fotos; no incluye un formulario específico para corregir este contacto privado.

## 8. Elegir una dirección y ajustar el mapa

Este componente se utiliza en los formularios que necesitan o admiten ubicación y en la edición correspondiente. No se muestra en «La tengo conmigo» vinculado.

1. La persona escribe al menos tres caracteres de una dirección, barrio o lugar.
2. Se ofrecen sugerencias del país obtenido de la referencia del dispositivo, cuando está disponible. Sin esa referencia se utiliza el país configurado, Uruguay por defecto. La búsqueda prioriza cercanía cuando dispone de un origen válido.
3. Buscar cerca de mí solicita usar el dispositivo para mejorar la prioridad de los resultados. Un permiso ya concedido se puede reutilizar; escribir en el campo no fuerza una solicitud de permiso.
4. Usar mi ubicación actual selecciona el punto del dispositivo e intenta obtener una dirección legible. Si se rechaza el permiso, se puede seguir buscando manualmente.
5. Al seleccionar un resultado o un punto válido, el mapa se muestra automáticamente en la misma página.
6. Se puede arrastrar el pin, tocar otro punto o mover el pin con las flechas del teclado.
7. Al moverlo se guarda inmediatamente la nueva coordenada y se intenta actualizar la dirección. No se conserva la precisión GPS ni la dirección anterior como si siguieran siendo válidas.
8. Cambiar lugar permite iniciar otra búsqueda. El texto sin un resultado seleccionado no sustituye una ubicación válida.

Leaflet presenta el mapa; OpenStreetMap aporta los datos cartográficos. La búsqueda de direcciones usa el proveedor configurado. Publicar en Internet exige revisar la configuración y las condiciones de uso del proveedor elegido; que funcione localmente no habilita por sí mismo una cuota de producción.

## 9. Razas, colores y características

- Raza y colores ofrecen sugerencias propias de MascoMatch, con el ancho del campo, fondo claro y resaltado del sitio.
- Las sugerencias se filtran al escribir y reconocen mayúsculas y acentos. No impiden ingresar una raza o color que no figure en el catálogo.
- Las flechas del teclado recorren opciones, Enter elige una opción activa y Escape o un clic fuera cierran la lista.
- Otros colores admite hasta cinco valores separados por comas. Elegir una sugerencia completa el color que se está escribiendo y conserva los anteriores.
- Collar y prendas permiten indicar si existen, sus colores y una descripción. Los datos opcionales desconocidos pueden quedar sin completar.
- La raza se sugiere según perro o gato. El catálogo incorpora las razas recopiladas de las páginas de Purina y conserva las opciones anteriores y el ingreso libre.

Los mismos controles se usan en publicación general, detalles opcionales de reportes vinculados, editores y filtros del catálogo cuando corresponde.

## 10. Fotos, miniaturas y ampliación

### Al publicar

Se admiten JPEG, PNG y WebP, hasta 10 MiB por foto y hasta cinco fotos por reporte. Se selecciona la miniatura antes de enviar. En los avisos perdidos y reportes generales las fotos son opcionales; en el nuevo recorrido vinculado de mascota bajo cuidado se exige al menos una.

El servidor comprueba el archivo real, procesa la imagen y retira metadatos. Las fotos se almacenan como objetos privados y se sirven a través de rutas que verifican la visibilidad o los permisos que correspondan. Una dirección privada del almacenamiento no se publica como enlace de la foto.

### Después de publicar

Desde Fotos y miniatura en Mis avisos o en el editor de un reporte se pueden agregar o quitar imágenes y cambiar la principal, respetando el máximo. La miniatura elegida se usa en tarjetas y mapas.

La ficha de un aviso muestra la foto principal grande y las demás debajo en pequeño. El catálogo permite pasar por las fotos de una tarjeta sin abrir la ficha. Avisos y avistamientos permiten ampliar las fotos, recorrer la galería y cerrar el visor dentro del sitio.

Si el formulario general guardó el reporte pero falló una carga posterior de fotos, se informa esa situación: no se presenta todo el reporte como perdido. Se pueden agregar las fotos desde Mis avisos. Un avistamiento sin foto utiliza un indicador propio; no se le atribuye como evidencia la foto del aviso perdido.

## 11. Buscar y consultar publicaciones

### Catálogo `/perdidos`

Muestra avisos de pérdida activos y visibles de perros y gatos. Se puede buscar por nombre, zona, descripción o código público, y filtrar por especie, raza, color, fechas de pérdida, sexo, tamaño, fotos y collar. Se aplican los filtros al consultar y se navegan los resultados por páginas.

Las tarjetas incluyen estado, código, miniatura, características conocidas, localidad, fecha y autor público cuando corresponde. Abrir una tarjeta lleva a la ficha con galería, descripción y los dos botones de ayuda. Una ficha que ya no es pública informa que el aviso dejó de estar disponible.

### Mapa del inicio

Muestra búsquedas activas con ubicación aproximada. Pasar por el marcador o tocarlo abre una miniatura, desde la cual se puede abrir el aviso.

### Mapa completo `/mapa`

La interfaz ofrece Perdidos y Avistamientos. Los avisos de pérdida se distinguen en rojo y los avistamientos en azul, con marcadores y tarjetas de un mismo estilo. Los encontrados no forman parte de las capas, contador ni lista de esta pantalla.

Los reportes de la lista incluyen miniatura cuando hay foto. Los avistamientos abren detalles dentro del mapa: características, descripción, hora, zona, fotos ampliables y aviso relacionado si existe. Si el reporte pertenece a la cuenta que inició sesión, se ofrece el acceso a editarlo.

Las coordenadas públicas son aproximadas; no deben interpretarse como el lugar exacto privado de un avistamiento. Los reportes sin ubicación no producen un marcador válido.

## 12. Crear cuenta, confirmar correo e ingresar

### Registro independiente

**Entrada:** Crear cuenta en el menú de cuenta o `/crear-cuenta`; también se ofrece registro durante la publicación general.

1. Se indica nombre o apodo, correo y una contraseña de al menos 12 caracteres.
2. El servidor valida los datos y que el correo no esté registrado.
3. Se crea la cuenta y se programa un correo de confirmación.
4. El enlace abre `/confirmar-correo`. Es de un solo uso y vence a las 24 horas.
5. Una vez confirmado, la cuenta puede publicar y utilizar las operaciones que requieren correo verificado.

Puede reenviarse el enlace, con límites para evitar abuso. Una cuenta no confirmada puede iniciar sesión, pero no obtiene por ello autorización para publicar. El registro depende de que esté habilitado el servicio de correo; no se simula una confirmación cuando está desactivado.

### Inicio y cierre de sesión

Ingresar abre `/login`. Se validan correo y contraseña y que la cuenta esté activa. El destino se resuelve según el recorrido y la verificación pendiente. Si ya hay sesión, se continúa al espacio correspondiente sin volver a presentar un registro como si faltara crear una cuenta.

La web conserva la sesión en una cookie HttpOnly; en producción se configura además como Secure. El servidor mantiene expiración y revocación. Cerrar sesión invalida esa sesión y actualiza el menú, Mis avisos y el acceso a Notificaciones.

### Recuperación de contraseña

1. Desde Olvidé mi contraseña se abre `/recuperar` y se escribe el correo.
2. Se presenta una respuesta que no revela públicamente si esa dirección tiene cuenta.
3. Para una cuenta habilitada se programa un enlace de un solo uso, válido durante 30 minutos.
4. El enlace permite establecer la nueva contraseña. Si venció o ya se utilizó, debe pedirse otro.
5. El cambio revoca las sesiones anteriores; el usuario vuelve a ingresar con la nueva contraseña. Este enlace válido también confirma el control del correo de esa cuenta.

## 13. Modificar datos de Mi cuenta

**Entrada:** menú de cuenta → Mi cuenta, `/mi-cuenta`.

| Acción | Recorrido y resultado |
| --- | --- |
| Cambiar nombre o teléfono | Se editan y guardan los datos. Al confirmarse el guardado aparece un modal y luego el mensaje junto al formulario. |
| Cambiar correo | Se solicita contraseña actual y la nueva dirección. El correo anterior continúa funcionando hasta confirmar el enlace enviado al nuevo. |
| Confirmar correo nuevo | El enlace vence a las 24 horas y se utiliza una sola vez. Se cambia la dirección, se cierran las sesiones anteriores y se ingresa con el correo nuevo. |
| Reenviar o cancelar cambio de correo | Se realiza desde Mi cuenta mientras existe una dirección pendiente. Un enlace anterior no puede confirmar otra dirección distinta. |
| Cambiar contraseña con sesión | Se ingresa la contraseña actual, una nueva y su confirmación. Se conservan la sesión actual y la verificación; se revocan las otras sesiones y los enlaces de recuperación pendientes. |
| Preferencias de correo | La casilla de Notificaciones guarda la preferencia en la misma página. Afecta alertas y recordatorios; no elimina la bandeja ni desactiva los correos de acceso solicitados. |

### Foto de perfil

Se puede subir una foto de hasta 10 MiB, moverla dentro del círculo, ajustar el zoom, guardar, reemplazar, quitar o ajustar el encuadre de la foto actual. Se utiliza en el menú de cuenta y en reseñas públicas no anónimas. Sin foto se muestran iniciales.

La foto de perfil no se procesa para buscar coincidencias de mascotas. Publicar una reseña como Anónimo oculta también la foto del perfil en esa reseña.

### Eliminar cuenta

1. En Mi cuenta se abre la sección de eliminación, se ingresa la contraseña y se escribe `ELIMINAR`.
2. Se elimina la cuenta, sus mascotas y avisos perdidos, sesiones, enlaces de acceso y los registros asociados que correspondan, incluidas sus reseñas.
3. Sus avistamientos y reportes de mascotas encontradas se conservan sin autor identificado y sin el consentimiento de compartir el contacto de la cuenta.
4. También se elimina el contacto privado que esa cuenta haya dejado en los nuevos reportes vinculados de mascota bajo cuidado.
5. Las fotos que deben desaparecer del almacenamiento se retiran mediante una cola de borrado que reintenta fallos.

Este borrado no restaura cuentas desde la web ni reescribe las copias históricas de respaldo. Si el contacto se dejó en un reporte anónimo, no existe una cuenta autora que permita asociarlo automáticamente con una eliminación de cuenta posterior.

## 14. Modificar avisos y reportes propios

### Aviso de mascota perdida

Se entra desde Mis avisos → Editar o desde Editar mi aviso en la ficha pública, si la sesión pertenece al dueño. El acceso directo utiliza `/mis-avisos?editar=…`.

Se pueden corregir datos de la mascota, características, fecha, descripción y lugar. En Descripción aparece el texto original, sin información de IA o líneas agregadas posteriormente. Si no se elige otro lugar, se conserva el existente. Las fotos y la miniatura se administran en su sección propia.

Guardar conserva el código del aviso y actualiza los datos utilizados por el análisis y la comparación. Recalcular la IA no reemplaza una respuesta humana anterior como si fuera una nueva confirmación del dueño.

### Avistamiento o mascota encontrada

El autor puede entrar desde Reportes que compartiste en Mis avisos, desde el acceso de edición de un reporte propio en el mapa o desde la confirmación posterior al envío. El editor utiliza `/mis-avisos/avistamientos/ID/editar`.

En reportes generales se pueden corregir especie, sexo, tamaño, características, descripción, fecha, lugar y la elección de compartir contacto cuando se ofrece. En los vinculados se conserva el vínculo al aviso y se editan los datos que correspondan a ese recorrido. La mascota bajo cuidado vinculada no vuelve a exigir ubicación ni fecha de hallazgo. Las fotos se gestionan por separado.

El servidor exige titularidad y correo confirmado para editar. Un nombre o teléfono indicado en un reporte breve no crea una cuenta ni convierte en autor a quien se registra después: un envío anónimo no tiene un editor de cuenta para reclamarlo posteriormente.

La API tiene operaciones autenticadas de eliminación definitiva de publicaciones propias. En la pantalla de gestión de avisos perdidos, Cerrar aviso es una acción de estado, distinta de borrar el registro.

## 15. Revisar coincidencias y cerrar una búsqueda

El dueño puede abrir Avistamientos y coincidencias en Mis avisos o abrir una notificación. Se distinguen los reportes enviados expresamente para su aviso y las recomendaciones surgidas de otros reportes.

| Respuesta | Qué significa | Efecto sobre el aviso |
| --- | --- | --- |
| Podría ser, todavía no estoy seguro | El reporte resulta relevante, pero no se reconoce la identidad con certeza. | Sigue activo. En mascota bajo cuidado, no revela el contacto. |
| No es mi mascota | Se descarta esa relación. | Sigue activo; se retira la alerta asociada de las vistas elegibles. |
| Es mi mascota, sigo buscándola | Se reconoce a la mascota en un avistamiento. | Sigue activa la búsqueda. |
| Es mi mascota, ver contacto | Se reconoce a la mascota en un reporte vinculado de alguien que la tiene. | Revela el contacto privado; sigue activa hasta la entrega. |
| Ya la recuperé / Marcar como encontrado | El dueño confirma la recuperación y responde cómo volvió, o elige no responder esa pregunta. | Pasa a `FOUND` y deja de mostrarse como pérdida activa. |
| Cerrar aviso | Se da por terminada la búsqueda sin afirmar una recuperación. | Pasa a `CLOSED` y deja el catálogo activo. |
| Reabrir búsqueda | Se reactiva un aviso retirado de una especie admitida. | Pasa a `ACTIVE` y vuelve a ser elegible para publicación y comparación. |

El código público no cambia. Cerrar o recuperar un aviso retira las alertas que ya no corresponden a una búsqueda activa y permite pedir una reseña. Reabrirlo retira temporalmente de la portada la reseña de esa búsqueda cerrada.

Reconocer una mascota en una foto, informar que otra persona la tiene y recuperarla físicamente son tres hechos diferentes. El sistema conserva esa distinción.

## 16. Notificaciones y correos

### Bandeja privada

Notificaciones aparece con sesión y abre en Sin leer. Abrir una alerta individual la marca como leída. También se puede marcar una, marcar todas, archivar o restaurar una archivada.

Marcar como leída la retira de Sin leer, pero continúa en Todas. Archivar la mueve a Archivadas; restaurar conserva la fecha de lectura y no reenvía el correo. No se modifican con esas acciones el aviso, las fotos ni la respuesta de identidad. Las operaciones se guardan en el servidor y el contador del menú se actualiza.

### Qué dispara cada correo

| Correo | Disparador | Condiciones principales |
| --- | --- | --- |
| Confirmación de cuenta | Registro o reenvío solicitado. | Dirección pendiente de confirmar; enlace de 24 horas. |
| Recuperación de contraseña | Solicitud para una cuenta habilitada. | Respuesta pública genérica; enlace de 30 minutos. |
| Confirmación de correo nuevo | Cambio solicitado desde Mi cuenta. | Contraseña validada; se envía al nuevo destinatario pendiente. |
| Alerta por avistamiento vinculado | Recepción de un reporte dirigido a un aviso. | Dueño distinto del autor; aviso y reporte elegibles. La revisión automática no impide que llegue la pista. |
| Alerta de mascota bajo cuidado | Recepción desde La tengo conmigo de un aviso. | Incluye el contexto de la mascota y acceso a revisar fotos; no adelanta el nombre ni teléfono. |
| Alerta por coincidencia general | El motor encuentra evidencia suficiente en otro reporte. | Umbrales y elegibilidad de la comparación general. |
| Resumen de reportes | Hay varias alertas pendientes para una misma búsqueda. | Se agrupan antes de enviar; no se confunden varios reportes con una sola identidad confirmada. |
| Recordatorio de fotos | Vence la espera del aviso perdido sin imágenes. | Búsqueda activa sin fotos, correo confirmado y preferencia habilitada. |
| Contacto a administración | Se recibe un formulario de Contacto y sugerencias. | Se reenvía a `info@mascomatch.com`; no responde automáticamente al visitante. |

Los correos usan la identidad visual del sitio, logo y botones de acción. SMTP aceptado no equivale a lectura ni garantiza que el mensaje haya llegado a la bandeja principal del destinatario.

Las alertas se guardan primero en la base. El envío en segundo plano comprueba visibilidad, cuenta, verificación y preferencia de correo. Leer, archivar, descartar o cerrar una búsqueda puede cancelar un correo todavía pendiente. Los fallos tienen reintentos y estado de entrega; la notificación web no depende de que SMTP esté disponible.

Los modos de entrega son `smtp`, `preview` y `disabled`. Preview se utiliza con un buzón de pruebas como Mailpit. El documento no presupone cuál está elegido en una instalación.

## 17. IA y comparación en segundo plano

1. Crear o modificar evidencia programa trabajos persistidos en la base, con referencia a la publicación, versión y modelo.
2. Un despachador entrega los pendientes a Redis/RQ. Si ese despacho falla, no se elimina por ello el aviso ni la tarea pendiente.
3. Los workers procesan descripciones y fotos. Gemma extrae características; Pet-ReID obtiene representaciones visuales para perros y gatos. OpenCLIP puede actuar como alternativa configurada.
4. Los resultados mantienen su origen y vigencia. Una tarea vieja no debe sustituir el resultado de una edición más reciente.
5. En la comparación general se revisan especie, características, fotos, zona y tiempo para formar candidatos y decidir alertas. Un porcentaje de compatibilidad no certifica identidad.
6. En La vi vinculado se conserva la pista aunque la comparación no la considere compatible.
7. En La tengo conmigo vinculado se solicita revisión humana sin condicionar el envío a ubicación, fecha o aprobación automática.
8. Un fallo de modelo conserva el reporte y deja registrado el estado del trabajo. Hay reintentos y herramientas para reprogramar tareas o completar análisis faltantes.

Los modelos son locales al entorno de servidores configurado; no requieren una API de IA paga para este recorrido. No se descargan pesos durante una solicitud de un visitante. Las claves SMTP, la cuenta del usuario y las coordenadas no se agregan como campos de entrada del modelo. El texto original que escriba una persona sí debe tratarse como su contenido aportado.

La API tiene consultas de análisis propio y operaciones autorizadas de solicitud y reintento; el panel administrativo permite inspeccionar los trabajos. Eso no significa que todas las herramientas técnicas de análisis tengan un botón en cada pantalla pública.

## 18. Reseñas de la comunidad

1. Después de cerrar un aviso perdido o marcar la recuperación, se ofrece al dueño compartir su experiencia.
2. Es opcional: omitirla no impide cerrar el aviso ni afecta la comparación.
3. Se eligen de una a cinco estrellas, se escribe un comentario y se autoriza expresamente su publicación. Se puede usar un nombre o apodo, o dejarlo vacío para publicar como Anónimo.
4. Se admite una reseña por aviso y se comprueba la titularidad y el cierre en el servidor.
5. La portada muestra las reseñas elegibles. Si no hay ninguna, no aparece la sección ni un bloque vacío.
6. Las reseñas con nombre pueden mostrar la foto actual del perfil; las anónimas no muestran esa foto. Ver más reseñas despliega las restantes disponibles.
7. El dueño puede retirar su reseña. El administrador puede ocultar o restaurar las que siguen siendo moderables, pero no volver a publicar una retirada por el propio autor.

## 19. Denunciar publicaciones y contactar a administración

### Denuncias

Desde Denunciar publicación se elige un motivo —spam, información falsa, foto inapropiada u otro— y se puede agregar detalle. Se admite con o sin cuenta.

La denuncia se registra y aparece en Administración → Denuncias y correcciones. No oculta automáticamente el aviso ni genera por sí misma un correo a administración. La cuenta administradora puede descartarla, ocultar o restaurar la publicación y bloquear a un autor identificado. Una publicación anónima se puede ocultar, pero no tiene una cuenta autora que bloquear.

### Contacto y sugerencias

**Entrada:** `/contacto`, desde Explorar o el footer. No exige sesión.

Se indica nombre, correo declarado, tipo de consulta y mensaje. Se aplican validaciones, controles antispam y límites de envío. La confirmación se presenta después de guardar el mensaje, aunque SMTP todavía no haya completado el reenvío.

El mensaje queda disponible para administración y se programa su envío a `info@mascomatch.com`. Reply-To permite responder al correo indicado por la persona, que no se considera verificado. Los fallos de envío se registran y reintentan. No se envía un acuse automático a la dirección aportada.

## 20. Aportes voluntarios

**Entrada:** Apoyanos en el encabezado, los CTA del inicio o Cómo apoyarnos en el footer; pantalla `/apoyanos`.

1. Se elige un nivel sugerido o un monto entero propio en pesos uruguayos. La publicación y búsqueda de mascotas siguen siendo gratuitas.
2. Si Mercado Pago está habilitado y configurado, el servidor registra la intención y crea la operación con una referencia que permite reintentar sin duplicarla.
3. La persona completa el checkout alojado por Mercado Pago. MascoMatch no solicita tarjetas en su formulario.
4. Al regresar a `/apoyanos/resultado`, se consulta el estado. El mero regreso a una URL de éxito no acredita un cobro.
5. El webhook firmado y la consulta del servidor al proveedor validan monto, moneda, receptor, aplicación, referencia y entorno antes de confirmar el aporte.
6. Se contemplan estados pendientes, rechazos, cancelaciones, reembolsos y contracargos. Una cola persistida permite conciliar actualizaciones y reintentar fallos.
7. Administración → Aportes permite consultar los registros y distinguir pruebas de dinero real. Las devoluciones se gestionan en Mercado Pago, no desde un botón financiero del dashboard.

El recorrido implementado es de aportes puntuales; no crea suscripciones mensuales. Si la integración no está habilitada, seleccionar un monto no significa que se haya cobrado. El acceso posterior al resultado de un aporte anónimo utiliza la referencia y la cookie privada del mismo navegador, no una cuenta creada automáticamente.

## 21. Administración, moderación y medición

La cuenta administradora debe estar activa, tener el correo confirmado y estar asignada como administradora única en la base. La asignación se realiza desde el servidor, no desde un registro público. Debe configurarse también en una base nueva de producción.

| Área | Flujo disponible |
| --- | --- |
| Resumen y actividad | Consultar usuarios, actividad reciente, publicaciones, trabajos, correos y contactos en el período. |
| Usuarios | Buscar y filtrar; consultar datos y actividad; bloquear o reactivar con motivo. |
| Publicaciones | Revisar avisos y reportes; ocultar o restaurar con motivo y controles de acceso. |
| Denuncias y correcciones | Revisar denuncias, tomar acciones y utilizar las herramientas de corrección habilitadas. |
| Trabajos | Consultar pendientes, ejecución, completados, fallos, modelos, intentos y fechas. |
| Correos | Consultar intentos de entrega y la cola; distinguir envíos reales de vistas previas. |
| Contactos | Leer los mensajes recibidos y revisar el estado del reenvío por correo. |
| Coincidencias | Seguir recomendaciones únicas y respuestas: confirmadas, falsas, dudosas y sin respuesta. |
| Analytics | Revisar recorridos, publicaciones e impacto con filtros; exportar agregados en CSV donde se ofrece esa acción. |
| Aportes | Revisar operaciones, entorno, estados, montos y conciliación. |
| Respaldos | Consultar el estado local y externo que informe el servicio de backup; no restaura desde la web. |
| Auditoría | Consultar las acciones administrativas, sus referencias y motivos. |

Las ventanas tienen actualización de datos sin recargar toda la página mediante el botón flotante. Se conservan los filtros aplicados. Las fechas y horas del panel se presentan con el criterio de Uruguay, y cada sección explica qué fecha está filtrando.

Bloquear una cuenta restringe su acceso y la visibilidad elegible de sus publicaciones; reactivarla no equivale a borrar el historial de moderación. Ocultar una publicación es diferente de eliminarla físicamente. Las acciones administrativas quedan auditadas.

Las métricas de coincidencias usan pares únicos y respuestas humanas. Una pista enviada desde una ficha no se cuenta automáticamente como una recomendación de IA. La tasa de confirmadas frente a falsas describe las respuestas obtenidas: no mide por sí sola todos los aciertos y omisiones posibles del modelo.

### Registro de actividad y analytics

Cuando está habilitado, el sistema registra eventos del recorrido y hechos confirmados por la API. Se utilizan identificadores propios seudónimos, sesiones de visita y agregados; no se interpreta cada petición HTTP como una visita humana. Los eventos tienen retención y limpieza programada. La decisión de habilitar estas cookies en la instalación corresponde a su configuración y política aplicable.

## 22. Respaldos completos y recuperación de información

Estos procesos pertenecen a la operación del servidor. No se activan por publicar un aviso ni por abrir el dashboard. La instalación local de desarrollo y el despliegue de producción no tienen necesariamente los mismos servicios ni destinos.

### 22.1. Qué incluye una copia completa

El proceso implementado genera un `.mbak` cifrado que contiene un volcado de PostgreSQL, las fotos referenciadas y los avatares, más un manifiesto con hashes de integridad. El volcado incluye usuarios y hashes de contraseñas, avisos, reportes, contactos privados de encontrados, coincidencias, tareas, estados de correo, moderación, aportes y demás tablas de la aplicación.

Las fotos operativas usan almacenamiento privado compatible con S3. En desarrollo se utiliza MinIO; el Compose de producción utiliza SeaweedFS. B2 es un destino externo para respaldos cifrados, no el almacenamiento cotidiano de cada foto.

La copia de datos no sustituye la conservación del código, configuración del despliegue y claves privadas necesarias para recuperar el servicio. La clave de cifrado del respaldo debe conservarse por separado: no se puede recuperar una copia cifrada perdiendo también su clave. Los modelos instalados y sus pesos no se incluyen como si fueran fotos de usuarios.

### 22.2. Creación periódica en el servidor

1. El servicio `backup`, cuando está levantado, inicia el ciclo de respaldo.
2. Obtiene una instantánea consistente de la base y el conjunto de objetos de fotos referenciados.
3. Genera el archivo cifrado en una ruta temporal, completa la escritura y verifica el archivo, la autenticación y los hashes.
4. Solo una copia que supera esas comprobaciones se registra como exitosa. Un error queda en el estado de operación para revisión y reintento.
5. Se aplica la retención local cuando corresponde.

Los valores predeterminados del Compose de producción son una copia completa cada **6 horas** y **14 copias locales**. Son parámetros configurables. Tener esos valores en un archivo no demuestra que un contenedor esté ejecutándose ni que una copia reciente haya terminado bien.

### 22.3. Copia externa a Backblaze B2

1. El operador habilita `OFFSITE_BACKUP_ENABLED` y configura el bucket privado y las credenciales restringidas.
2. El servicio revisa el destino y sube únicamente los `.mbak` ya cifrados.
3. Comprueba la versión remota, el tamaño y la retención configurada. El diseño utiliza Object Lock COMPLIANCE por al menos 30 días, más el margen de transferencia que comprueba el proceso.
4. Si B2 falla, las copias locales pendientes de confirmación remota se conservan y se reintenta. No se eliminan pendientes solo para cumplir el número de copias locales.
5. Se realizan comprobaciones profundas mediante descarga y autenticación según el período configurado.
6. Las reglas de vencimiento remoto se configuran en el proveedor; la aplicación no borra automáticamente objetos remotos para evitar un bloqueo de retención.

La copia externa está desactivada por defecto. Sus credenciales, bucket, reglas de retención y comprobaciones reales deben prepararse en el entorno que vaya a operar. El estado se puede consultar por las herramientas operativas y el widget administrativo. Una caída prolongada exige vigilar el espacio local.

### 22.4. Restauración

La recuperación es una operación manual del responsable sobre otro entorno o destinos vacíos, con la aplicación detenida. El flujo de restauración no sobrescribe una base con tablas de aplicación ni un bucket de fotos con objetos existentes.

1. Se elige una copia local verificada o una versión remota de B2.
2. Si viene de B2, se descarga conservando la identificación de objeto y versión.
3. Antes de modificar los destinos se descifra, autentica y comprueba el manifiesto y los hashes.
4. Se restauran la base y las imágenes en la base y el bucket vacíos.
5. Se comprueban los datos, la configuración compatible y los servicios antes de volver a habilitar el sitio.

El procedimiento técnico completo y el simulacro con datos desechables están en [Respaldos externos en Backblaze B2](backblaze-backup.md). El dashboard informa estado; no ejecuta una restauración por clic.

### 22.5. Respaldo antes de actualizar y diferencias con Git

El procedimiento de despliegue construye la nueva versión, detiene API/workers/backup, prepara los servicios de datos y crea una copia completa local antes de migrar una instalación existente. Luego aplica las migraciones, prepara los modelos que correspondan, inicia los servicios y ejecuta las comprobaciones de la versión.

Un `pg_dump` manual protege la base, pero por sí solo no es la copia completa de fotos y base en `.mbak`. Las copias manuales realizadas durante el desarrollo no prueban que esté activo el ciclo automático de producción.

Un commit y push protegen el código del repositorio. No suben la base, fotos privadas, archivos `.env`, secretos ni los respaldos ignorados por Git, y no sustituyen la copia operativa de datos. Volver a un commit tampoco revierte automáticamente una migración de base.

## 23. Despliegue, trabajos automáticos y carga visual

El despliegue preparado utiliza contenedores en un servidor Linux, HTTPS, redes privadas para los servicios internos y secretos montados según el servicio. Publicar el repositorio no configura por sí mismo el dominio ni enciende un servidor. Cuando se despliega allí, estos procesos corren en el servidor y no necesitan que la PC de desarrollo permanezca encendida.

| Proceso automático | Qué lo dispara o mantiene |
| --- | --- |
| Despacho de IA | Trabajos pendientes y servicios de análisis habilitados. |
| Comparación | Reportes y evidencias nuevos o modificados; reevaluación de pendientes. |
| Correos de acceso | Solicitudes de registro, confirmación, cambio de correo y recuperación guardadas. |
| Alertas | Notificaciones elegibles pendientes, preferencias y comprobaciones de entrega. |
| Recordatorios de fotos | Avisos sin imágenes cuyo plazo vence. |
| Reenvío de contacto | Mensajes recibidos aún pendientes de envío a administración. |
| Limpieza de imágenes | Objetos programados para eliminación tras borrar datos. |
| Registro y limpieza de métricas | Actividad, eventos y períodos de retención configurados. |
| Conciliación de aportes | Webhooks y consultas de recuperación de operaciones pendientes. |
| Respaldos | Servicio de backup activo y su intervalo configurado. |

Las pantallas de carga de página usan el logo y el perro animado de MascoMatch a toda la altura visible, también en celular. Conservan el mensaje de la operación en curso y desaparecen con el resultado o error. Las cargas parciales de mapas o tarjetas utilizan un indicador pequeño. La preferencia de reducir movimiento selecciona una imagen quieta del perro.

No se agrega una espera artificial para mostrar la animación. Las respuestas de error ofrecen el mensaje o reintento correspondiente; consultar de nuevo no debe publicar otro aviso o duplicar un envío ya guardado.

## 24. Estados que no deben confundirse

| Estado o situación | Interpretación correcta |
| --- | --- |
| Aviso `ACTIVE` | La búsqueda sigue abierta. |
| Aviso `FOUND` | El dueño registró la recuperación. |
| Aviso `CLOSED` | La búsqueda se cerró sin afirmar recuperación. |
| Aviso `CANCELLED` | Estado de cancelación admitido por el modelo/API. La acción habitual de cierre en la web es Cerrar aviso. |
| Moderación `HIDDEN` | El contenido está oculto; no equivale a borrarlo físicamente ni a recuperar una mascota. |
| Reporte `FOUND_ANIMAL` | Otra persona informa una mascota encontrada; no cambia por sí mismo el aviso perdido a `FOUND`. |
| Comparación pendiente | El reporte está guardado, pero el análisis no terminó. |
| Identidad por confirmar | Hace falta revisión humana; no es una identificación automática cierta. |
| Respuesta `CONFIRMED_RELEVANT` | El dueño considera posible la pista, todavía sin confirmar identidad. |
| Respuesta `RESOLVED` | El dueño reconoce a la mascota. El cierre por recuperación es otra acción, salvo que se confirme junto con ella. |
| Notificación leída o archivada | Estado de la bandeja, sin modificar por sí solo el aviso. |
| Correo enviado | El transporte lo aceptó; no prueba lectura ni recepción en bandeja principal. |
| Contacto guardado | Se recibió el mensaje de contacto; el reenvío SMTP puede seguir pendiente. |
| Aporte pendiente | Aún no hay confirmación válida del proveedor. |
| Backup local exitoso | Se verificó la copia local; la confirmación de la copia externa es un control adicional. |

## 25. Guías técnicas y operativas

El comportamiento de los recorridos se concentra en este documento. Las guías siguientes describen sus componentes, configuración, métricas y operación sin mantener una guía independiente por cada cambio.

| Área | Guía |
| --- | --- |
| Tecnologías, datos, privacidad e invariantes | [Arquitectura](architecture.md) |
| Formularios, mapas, sugerencias, imágenes y cargas | [Frontend](frontend.md) |
| Usuarios, moderación, recomendaciones y panel privado | [Administración](admin-operations.md) |
| Visitas, exposiciones, respuestas e impacto | [Métricas](analytics.md) |
| Modelos, colas, reglas y evaluación | [IA local](ai-production.md) |
| Procedencia y artefactos de modelos | [Modelos de terceros](third-party-models.md) |
| Primer despliegue | [Puesta en producción](puesta-en-produccion-paso-a-paso.md) |
| Actualizaciones, correo y respaldos locales | [Operación del servidor](production.md) |
| Copia externa y recuperación | [Backblaze B2](backblaze-backup.md) |
| Aportes puntuales | [Mercado Pago](mercado-pago-configuracion.md) |
| Mediciones técnicas fechadas | [Benchmarks históricos](benchmarks/README.md) |

La habilitación externa de SMTP, IA, mapas, pagos, monitoreo y B2 se comprueba en el entorno de despliegue; no se deduce del hecho de que el código o estas guías estén en GitHub.
