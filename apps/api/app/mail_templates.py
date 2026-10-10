"""Branded transactional content, with plain text and an embedded logo."""
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape
from pathlib import Path


LOGO_PATH = Path(__file__).parent / "assets" / "mascomatch-mark.png"


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
    logo_cid = make_msgid(domain="mascomatch.com")
    safe_url = escape(url, quote=True)
    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Recuperá tu cuenta de MascoMatch</title>
</head>
<body style="margin:0;padding:0;background-color:#f6f7fb;color:#0b2a4a;font-family:Arial,Helvetica,sans-serif;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all;">Elegí una nueva contraseña para volver a ingresar a MascoMatch.</div>
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
              <p style="margin:0 0 12px;font-size:12px;line-height:18px;font-weight:700;letter-spacing:1.4px;color:#0863b4;">RECUPERACIÓN DE CUENTA</p>
              <h1 style="margin:0 0 16px;font-size:28px;line-height:36px;font-weight:700;color:#0b2a4a;">Recuperá tu acceso</h1>
              <p style="margin:0 0 24px;font-size:16px;line-height:26px;color:#52677e;">Recibimos una solicitud para cambiar la contraseña de tu cuenta de MascoMatch. Elegí una nueva contraseña para volver a ingresar.</p>
              <table role="presentation" border="0" cellspacing="0" cellpadding="0" style="margin:0 0 24px;">
                <tr>
                  <td align="center" bgcolor="#d93646" style="border-radius:10px;">
                    <a href="{safe_url}" style="display:inline-block;padding:14px 24px;border:1px solid #d93646;border-radius:10px;color:#ffffff;text-decoration:none;font-size:16px;line-height:24px;font-weight:700;">Elegir nueva contraseña</a>
                  </td>
                </tr>
              </table>
              <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#fff1f2" style="border-radius:10px;">
                <tr>
                  <td style="padding:14px 16px;font-size:14px;line-height:22px;color:#0b2a4a;"><strong>Tenés 30 minutos</strong><br>El enlace vence a los 30 minutos de solicitarlo y se puede usar una sola vez.</td>
                </tr>
              </table>
              <p style="margin:24px 0 8px;font-size:13px;line-height:21px;color:#52677e;">Si el botón no funciona, copiá y pegá este enlace en tu navegador:</p>
              <p style="margin:0;font-size:13px;line-height:21px;word-break:break-all;overflow-wrap:anywhere;"><a href="{safe_url}" style="color:#0863b4;text-decoration:underline;word-break:break-all;">{safe_url}</a></p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 28px;border-top:1px solid #e5eaf0;">
              <p style="margin:0;font-size:13px;line-height:21px;color:#52677e;">Si no pediste este cambio, podés ignorar este correo. Tu contraseña seguirá siendo la misma.</p>
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
