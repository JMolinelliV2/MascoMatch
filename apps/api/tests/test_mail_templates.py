from datetime import datetime, timezone
from email.message import EmailMessage
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.config import settings
from app.mail_templates import (
    add_delivery_check_content,
    add_email_change_content,
    add_email_verification_content,
    add_password_reset_content,
)
from app.notifications.email import build_message
from app.photo_albums import MAX_REPORT_PHOTOS
from app.photo_reminders import build_message as photo_message


def contents(message):
    plain = message.get_body(preferencelist=("plain",)).get_content()
    html = message.get_body(preferencelist=("html",)).get_content()
    # The logo must remain usable without a public image server.
    logo = next(part for part in message.walk() if part.get_content_type() == "image/png")
    assert logo.get_content_disposition() == "inline"
    assert f"cid:{str(logo['Content-ID'])[1:-1]}" in html
    assert logo.get_payload(decode=True).startswith(b"\x89PNG")
    assert "#d93646" in html and 'align="center"' in html
    return plain, html


def notice(**changes):
    return SimpleNamespace(id=uuid4(), title="Reportaron un avistamiento para Luna",
                           body="La identidad está por confirmar.", **changes)


def test_photo_reminder_advises_several_photos_and_escapes_the_pet_name():
    case = SimpleNamespace(id=uuid4())
    owner = SimpleNamespace(email="owner@example.test")
    message = photo_message(case, SimpleNamespace(name='Luna <script>alert("x")</script>'), owner)
    plain, html = contents(message)
    assert f"hasta {MAX_REPORT_PHOTOS} fotos" in plain
    for advice in ("de frente", "cuerpo entero", "de perfil", "rasgos distintivos", "luz natural", "miniatura"):
        assert advice in plain and advice in html
    assert "Agregar fotos" in html and "Agregar una foto" not in html
    assert "Varias fotos" in message["Subject"]
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert f"/mis-avisos?foto={case.id}#fotos-{case.id}" in plain
    assert "/mi-cuenta#notificaciones" in plain and "/mi-cuenta#notificaciones" in html
    assert message["To"] == owner.email


def test_single_alert_keeps_its_evidence_time_links_and_untrusted_text_safe(monkeypatch):
    monkeypatch.setattr(settings, "public_site_url", "https://mascomatch.example")
    report = SimpleNamespace(id=uuid4(), title='Luna <img src=x onerror="alert(1)">',
                             body="La comparación detectó diferencias. <script>alert(1)</script>")
    observation = SimpleNamespace(observed_at=datetime(2026, 11, 2, 18, 30, tzinfo=timezone.utc),
                                  public_location='Zona <b>de ejemplo</b>', latitude=-34.90123, longitude=-56.15234)
    owner = SimpleNamespace(email="owner@example.test")
    message = build_message(report, owner, observation)
    plain, html = contents(message)
    assert report.body in plain
    assert "02/11/2026 15:30 (hora de Uruguay)" in plain
    assert "02/11/2026 15:30 (hora de Uruguay)" in html
    assert "Zona &lt;b&gt;de ejemplo&lt;/b&gt;" in html
    assert "<script>" not in html and "<img src=x" not in html
    assert "Revisar avistamiento" in html
    for body in (plain, html):
        assert f"/notificaciones?aviso={report.id}" in body
        assert "/mi-cuenta#notificaciones" in body
        assert "-34.90123" not in body and "-56.15234" not in body
    assert message["To"] == owner.email


def test_alert_without_context_does_not_invent_a_date_or_zone():
    message = build_message(notice(), SimpleNamespace(email="owner@example.test"))
    plain, html = contents(message)
    for body in (plain, html):
        assert "Fecha del avistamiento" not in body
        assert "Zona:" not in body
        assert "por confirmar" in body


def test_grouped_alert_keeps_all_plain_links_and_bounds_the_html_summary():
    reports = [notice() for _ in range(100)]
    message = build_message(reports[0], SimpleNamespace(email="owner@example.test"), related=reports)
    plain, html = contents(message)
    assert "100 reportes nuevos" in message["Subject"]
    assert all(str(report.id) in plain for report in reports)
    assert all(str(report.id) in html for report in reports[:5])
    assert str(reports[5].id) not in html
    assert "95 reportes más" in html
    assert "Ver todos los avistamientos" in html
    assert "/mi-cuenta#notificaciones" in html
    assert len(html.encode("utf-8")) < 50_000


def test_one_related_alert_keeps_the_single_report_view():
    report = notice()
    message = build_message(report, SimpleNamespace(email="owner@example.test"), related=[report])
    _, html = contents(message)
    assert "Revisar avistamiento" in html
    assert message["Subject"] == report.title


@pytest.mark.parametrize("renderer", [add_password_reset_content, add_email_verification_content, add_email_change_content])
def test_account_templates_retain_their_link_logo_and_separate_security_purpose(renderer):
    message = EmailMessage()
    renderer(message, "https://mascomatch.example/confirmar-correo?codigo=fake&purpose=example")
    plain, html = contents(message)
    assert "codigo=fake&purpose=example" in plain
    assert 'href="https://mascomatch.example/confirmar-correo?codigo=fake&amp;purpose=example"' in html
    assert "Configurar notificaciones" not in html


def test_operator_delivery_check_also_has_the_branded_html_version():
    message = EmailMessage()
    add_delivery_check_content(message, "https://mascomatch.example")
    plain, html = contents(message)
    assert "solicitado por la administración" in plain
    assert "COMPROBACIÓN DE CORREO" in html
