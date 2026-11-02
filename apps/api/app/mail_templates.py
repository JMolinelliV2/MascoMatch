"""Branded transactional content, with plain text and an embedded logo."""
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape
from pathlib import Path


LOGO_PATH = Path(__file__).parent / "assets" / "mascomatch-mark.png"
PHOTO_TIPS = (
    "Una foto de frente, con la cara y los ojos bien visibles.",
    "Una de cuerpo entero y de perfil, para ver la silueta, las patas y la cola.",
    "Otro ángulo y acercamientos de manchas, orejas, collar u otros rasgos distintivos.",
    "Usá fotos recientes, bien enfocadas y con luz natural; evitá filtros, texto y recortes que tapen a la mascota.",
    "Elegí como miniatura la imagen más clara para reconocerla rápidamente.",
)


def add_password_reset_content(message: EmailMessage, url: str) -> None:
    message.set_content(
        "Recuperá tu acceso a MascoMatch\n\n"
        "Recibimos una solicitud para cambiar la contraseña de tu cuenta. "
        "Abrí este enlace para elegir una nueva contraseña:\n\n"
        f"{url}\n\n"
        "El enlace es de un solo uso y vence a los 30 minutos de solicitarlo.\n\n"
        "Si no pediste este cambio, podés ignorar este correo. "
        "Tu contraseña seguirá siendo la misma.\n\nMascoMatch"
    )
    _add_branded_html(message, url,
        preheader="Elegí una nueva contraseña para volver a ingresar a MascoMatch.",
        eyebrow="RECUPERACIÓN DE CUENTA", title="Recuperá tu acceso",
        description="Recibimos una solicitud para cambiar la contraseña de tu cuenta de MascoMatch. Elegí una nueva contraseña para volver a ingresar.",
        action="Elegir nueva contraseña", expiry_title="Tenés 30 minutos",
        expiry_text="El enlace vence a los 30 minutos de solicitarlo y se puede usar una sola vez.",
        footer="Si no pediste este cambio, podés ignorar este correo. Tu contraseña seguirá siendo la misma.")


def add_email_verification_content(message: EmailMessage, url: str) -> None:
    message.set_content(
        "Confirmá tu correo en MascoMatch\n\n"
        "Gracias por sumarte. Confirmá que este correo es tuyo para publicar avisos "
        "y recibir alertas de posibles avistamientos.\n\n"
        f"{url}\n\n"
        "El enlace es de un solo uso y vence a las 24 horas de solicitarlo.\n\n"
        "Si no creaste una cuenta ni pediste este enlace, podés ignorar este correo.\n\nMascoMatch"
    )
    _add_branded_html(message, url,
        preheader="Confirmá tu correo para empezar a publicar en MascoMatch.",
        eyebrow="CONFIRMACIÓN DE CORREO", title="Un paso más para empezar",
        description="Gracias por sumarte a MascoMatch. Confirmá que este correo es tuyo para publicar avisos y recibir alertas de posibles avistamientos.",
        action="Confirmar mi correo", expiry_title="Tenés 24 horas",
        expiry_text="El enlace vence a las 24 horas de solicitarlo y se puede usar una sola vez.",
        footer="Si no creaste una cuenta ni pediste este enlace, podés ignorar este correo.")


def add_email_change_content(message: EmailMessage, url: str) -> None:
    message.set_content("Confirmá tu nuevo correo en MascoMatch\n\n"
        "Pediste usar esta dirección para tu cuenta. Confirmá el cambio:\n\n"
        f"{url}\n\nEl enlace es de un solo uso y vence a las 24 horas. "
        "Tu correo actual seguirá funcionando hasta que confirmes el cambio. "
        "Después tendrás que ingresar de nuevo con esta dirección.\n\n"
        "Si no pediste este cambio, ignorá el mensaje.\n\nMascoMatch")
    _add_branded_html(message, url,
        preheader="Confirmá la nueva dirección de tu cuenta.",
        eyebrow="CAMBIO DE CORREO", title="Confirmá tu nuevo correo",
        description="Pediste usar esta dirección en MascoMatch. Tu correo actual seguirá funcionando hasta que confirmes el cambio. Después tendrás que ingresar de nuevo con esta dirección.",
        action="Confirmar nuevo correo", expiry_title="Tenés 24 horas",
        expiry_text="Este enlace vence a las 24 horas y se puede usar una sola vez.",
        footer="Si no pediste este cambio, podés ignorar el mensaje. Tu dirección actual seguirá siendo la misma.")


def add_photo_reminder_content(message: EmailMessage, pet_name: str, url: str, preferences_url: str) -> None:
    description = (f"Tu aviso de {pet_name} sigue activo y todavía no tiene fotos. "
                   "Agregá varias imágenes para que otras personas puedan reconocer a tu mascota desde distintos ángulos. "
                   "Podés cargar hasta 5 fotos y elegir cuál se muestra como miniatura.")
    tips_text = "\n".join(f"- {tip}" for tip in PHOTO_TIPS)
    message.set_content(
        "Varias fotos pueden ayudar a encontrar a tu mascota\n\n"
        f"{description}\n\nQué fotos elegir:\n{tips_text}\n\n"
        f"Agregá tus fotos desde Mis avisos:\n{url}\n\n"
        "Tu aviso sigue publicado aunque no agregues fotos.\n\n"
        f"Preferencias de correo:\n{preferences_url}\n\nMascoMatch"
    )
    _add_branded_html(message, url,
        preheader="Sumá varias fotos para que más personas puedan reconocer a tu mascota.",
        eyebrow="COMPLETÁ TU AVISO", title="Varias fotos pueden ayudar",
        description=description, action="Agregar fotos", expiry_title="Qué fotos elegir",
        expiry_text="Combiná distintas vistas de la misma mascota:", tips=PHOTO_TIPS,
        footer="Tu aviso sigue publicado aunque no agregues fotos.", preferences_url=preferences_url)


def add_sighting_alert_content(message: EmailMessage, title: str, body: str, url: str,
                               preferences_url: str, *, when: str | None = None,
                               location: str | None = None) -> None:
    details = []
    if when:
        details.append(("Fecha del avistamiento", when))
    if location:
        details.append(("Zona", location))
    context = "\n\n" + "\n".join(f"{label}: {value}" for label, value in details) if details else ""
    message.set_content(
        f"{title}\n\n{body}{context}\n\n"
        f"Revisá el lugar y las fotos en MascoMatch:\n{url}\n\n"
        "La identidad de la mascota necesita confirmación.\n"
        "Podés cambiar tus preferencias de correo en Mi cuenta:\n"
        f"{preferences_url}"
    )
    _add_branded_html(message, url,
        preheader="Revisá el lugar, las fotos y la fecha del reporte en MascoMatch.",
        eyebrow="AVISTAMIENTOS", title=title, description=body,
        action="Revisar avistamiento", details=tuple(details),
        expiry_title="La identidad está por confirmar",
        expiry_text="Compará las fotos, el lugar y la fecha antes de confirmar si se trata de tu mascota.",
        footer="Este reporte es una pista para revisar. Seguí las novedades desde tu cuenta.",
        preferences_url=preferences_url)


def add_grouped_sightings_content(message: EmailMessage, reports: list[tuple[str, str]],
                                 url: str, preferences_url: str) -> None:
    count = len(reports)
    links = "\n".join(link for _, link in reports)
    message.set_content(
        f"Recibimos {count} avistamientos potencialmente relacionados con el mismo aviso.\n\n"
        f"Revisá los lugares, fotos y motivos de cada reporte:\n{links}\n\n"
        "La identidad de las mascotas necesita confirmación.\n"
        f"Podés cambiar tus preferencias de correo en Mi cuenta:\n{preferences_url}"
    )
    _add_branded_html(message, url,
        preheader=f"Tenés {count} reportes nuevos para revisar en MascoMatch.",
        eyebrow="NOVEDADES DE TU AVISO", title=f"Tenés {count} avistamientos nuevos",
        description="Recibimos varios reportes que pueden estar relacionados con el mismo aviso. Revisá el lugar, las fotos y los motivos de cada uno.",
        action="Ver todos los avistamientos", report_links=tuple(reports[:5]), more_reports=max(0, count-5),
        expiry_title="Cada reporte necesita revisión",
        expiry_text="La identidad de la mascota está por confirmar. Podés revisar cada avistamiento desde tu cuenta.",
        footer="Agrupamos las novedades del mismo aviso para que puedas revisarlas juntas.",
        preferences_url=preferences_url)


def add_delivery_check_content(message: EmailMessage, url: str) -> None:
    description = "Este correo fue solicitado por la administración para comprobar la configuración de MascoMatch."
    message.set_content(f"{description}\n\nAbrir MascoMatch:\n{url}")
    _add_branded_html(message, url,
        preheader="Comprobación del envío de correos de MascoMatch.",
        eyebrow="COMPROBACIÓN DE CORREO", title="El correo está en camino",
        description=description, action="Abrir MascoMatch",
        expiry_title="Mensaje de comprobación",
        expiry_text="La recepción de este mensaje permite revisar la entrega y el diseño del correo.",
        footer="Esta comprobación fue solicitada por la administración de MascoMatch.")


def _add_branded_html(message: EmailMessage, url: str, *, preheader: str, eyebrow: str,
                      title: str, description: str, action: str, expiry_title: str,
                      expiry_text: str, footer: str, tips: tuple[str, ...] = (),
                      details: tuple[tuple[str, str], ...] = (),
                      report_links: tuple[tuple[str, str], ...] = (), more_reports: int = 0,
                      preferences_url: str | None = None) -> None:
    logo_cid = make_msgid(domain="mascomatch.com")
    safe_url = escape(url, quote=True)
    details_html = ""
    if details:
        rows = "".join(f'<tr><td style="padding:8px 16px;font-size:14px;line-height:22px;color:#52677e;word-break:break-word;overflow-wrap:anywhere;"><strong style="color:#0b2a4a;">{escape(label)}</strong><br>{escape(value)}</td></tr>' for label, value in details)
        details_html = f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" bgcolor="#eff8ff" style="margin:0 0 24px;border-radius:10px;">{rows}</table>'
    reports_html = ""
    if report_links:
        rows = "".join(f'<tr><td style="padding:14px 16px;border-bottom:1px solid #e5eaf0;word-break:break-word;overflow-wrap:anywhere;"><a href="{escape(link, quote=True)}" style="display:block;color:#0863b4;font-size:14px;line-height:22px;text-decoration:underline;"><strong>Reporte {index}</strong><br>{escape(label)}</a></td></tr>' for index, (label, link) in enumerate(report_links, 1))
        reports_html = f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 24px;border:1px solid #e5eaf0;border-radius:10px;">{rows}</table>'
        if more_reports:
            reports_html += f'<p style="margin:0 0 24px;color:#52677e;font-size:14px;line-height:22px;">Hay {more_reports} reportes más. Podés revisar todos en tu bandeja.</p>'
    tips_html = ""
    if tips:
        items = "".join(f'<li style="margin:0 0 10px;padding-left:2px;">{escape(tip)}</li>' for tip in tips)
        tips_html = f'<ul style="margin:12px 0 0;padding-left:20px;">{items}</ul>'
    preferences_html = ""
    if preferences_url:
        preferences_html = f'<p style="margin:12px 0 0;font-size:13px;line-height:21px;"><a href="{escape(preferences_url, quote=True)}" style="color:#0863b4;text-decoration:underline;">Configurar notificaciones en Mi cuenta</a></p>'
    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} — MascoMatch</title>
</head>
<body style="margin:0;padding:0;background-color:#f6f7fb;color:#0b2a4a;font-family:Arial,Helvetica,sans-serif;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all;">{escape(preheader)}</div>
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#f6f7fb">
    <tr>
      <td align="center" style="padding:32px 12px;">
        <!--[if mso]><table role="presentation" width="560" border="0" cellspacing="0" cellpadding="0"><tr><td><![endif]-->
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#ffffff" style="max-width:560px;border:1px solid #e5eaf0;border-top:5px solid #d93646;border-radius:16px;">
          <tr>
            <td style="padding:28px 28px 24px;border-bottom:1px solid #e5eaf0;">
              <table role="presentation" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td width="44" valign="middle"><img src="cid:{logo_cid[1:-1]}" width="44" height="44" alt="" style="display:block;border:0;"></td>
                  <td valign="middle" style="padding-left:10px;font-size:26px;line-height:32px;font-weight:800;letter-spacing:-0.8px;color:#0b2a4a;">Masco<span style="color:#d93646;">Match</span></td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:28px;">
              <p style="margin:0 0 12px;font-size:12px;line-height:18px;font-weight:700;letter-spacing:1.4px;color:#0863b4;">{escape(eyebrow)}</p>
              <h1 style="margin:0 0 16px;font-size:28px;line-height:36px;font-weight:700;color:#0b2a4a;">{escape(title)}</h1>
              <p style="margin:0 0 24px;font-size:16px;line-height:26px;color:#52677e;">{escape(description)}</p>
              {details_html}
              {reports_html}
              <table role="presentation" align="center" border="0" cellspacing="0" cellpadding="0" style="margin:0 auto 24px;">
                <tr>
                  <td align="center" bgcolor="#d93646" style="border-radius:10px;">
                    <a href="{safe_url}" style="display:inline-block;padding:14px 24px;border:1px solid #d93646;border-radius:10px;color:#ffffff;text-decoration:none;font-size:16px;line-height:24px;font-weight:700;">{escape(action)}</a>
                  </td>
                </tr>
              </table>
              <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#fff1f2" style="border-radius:10px;">
                <tr>
                  <td style="padding:14px 16px;font-size:14px;line-height:22px;color:#0b2a4a;"><strong>{escape(expiry_title)}</strong><br>{escape(expiry_text)}{tips_html}</td>
                </tr>
              </table>
              <p style="margin:24px 0 8px;font-size:13px;line-height:21px;color:#52677e;">Si el botón no funciona, copiá y pegá este enlace en tu navegador:</p>
              <p style="margin:0;font-size:13px;line-height:21px;word-break:break-all;overflow-wrap:anywhere;"><a href="{safe_url}" style="color:#0863b4;text-decoration:underline;word-break:break-all;">{safe_url}</a></p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 28px;border-top:1px solid #e5eaf0;">
              <p style="margin:0;font-size:13px;line-height:21px;color:#52677e;">{escape(footer)}</p>
              {preferences_html}
            </td>
          </tr>
        </table>
        <!--[if mso]></td></tr></table><![endif]-->
        <p style="margin:20px 0 0;font-size:12px;line-height:20px;color:#64748b;">MascoMatch · Más miradas, más oportunidades de reencontrarse.</p>
      </td>
    </tr>
  </table>
</body>
</html>"""
    message.add_alternative(html, subtype="html")
    # CID keeps the logo inside the email; no public image host is required.
    message.get_payload()[-1].add_related(
        LOGO_PATH.read_bytes(), maintype="image", subtype="png", cid=logo_cid,
        filename="mascomatch-logo.png", disposition="inline",
    )
