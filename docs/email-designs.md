# Diseños de correos

Los correos de cuenta, recordatorio de fotos, alertas de avistamientos individuales y agrupados y la comprobación técnica de correo tienen HTML con la identidad de MascoMatch y una alternativa de texto plano. Contacto ya utiliza su versión HTML. Los nueve escenarios de alertas comparten la plantilla de avistamientos; el título y el texto conservan las diferencias entre comparación pendiente, datos insuficientes, diferencias, fotos para revisar y posible coincidencia.

La estructura compartida en `app/mail_templates.py` mantiene el logo incrustado por CID, ancho máximo de 560 px, tipografía Arial, encabezado coral, fondos suaves y botón central. No depende de fuentes ni imágenes externas. Las preferencias se enlazan desde alertas y recordatorios, sin agregarlas a los correos de seguridad de cuenta.

Las alertas individuales incluyen fecha en horario de Uruguay y zona pública cuando existen. No agregan coordenadas precisas ni contactos ajenos. El botón conserva `/notificaciones?aviso=<id>`. El resumen agrupado presenta hasta cinco enlaces individuales y, cuando hay más, indica la cantidad restante y permite abrir la bandeja completa. Su alternativa de texto conserva todos los enlaces del grupo. El contenido variable se escapa antes de incorporarlo al HTML.

El recordatorio de fotos recomienda varias imágenes, hasta cinco, y ofrece consejos de frente, perfil, cuerpo entero, marcas distintivas, luz y enfoque. Permite elegir la miniatura; no cambia la condición de envío ni vuelve a recordar a quien ya tenga fotos.

El transporte SMTP, los destinatarios, las preferencias, los reintentos y la agrupación se mantienen en sus módulos existentes. Los cambios son de presentación y contenido. Las muestras de revisión utilizan datos ficticios y enlaces no asociados a cuentas reales.
