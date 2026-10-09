from datetime import timedelta
from sqlalchemy import select
from app import account_mail
from app.analysis.service import utcnow
from app.core.config import settings
from app.models import AccountToken, User


def latest_code(db_factory):
    with db_factory() as db:
        ticket=db.scalar(select(AccountToken).order_by(AccountToken.created_at.desc()))
        return account_mail.decrypt_token(ticket.encrypted_token)


def test_email_confirmation_is_single_use_and_preserves_login(client,auth_headers,db_factory):
    assert client.post("/api/v1/auth/request-verification",headers=auth_headers).status_code==200
    code=latest_code(db_factory)
    assert client.post("/api/v1/auth/verify-email",json={"code":code}).status_code==200
    assert client.post("/api/v1/auth/verify-email",json={"code":code}).status_code==400
    assert client.get("/api/v1/auth/me",headers=auth_headers).json()["email_verified"]


def test_reset_is_generic_single_use_and_revokes_existing_sessions(client,auth_headers,db_factory):
    known=client.post("/api/v1/auth/password-reset",json={"email":"owner@example.com"})
    unknown=client.post("/api/v1/auth/password-reset",json={"email":"unknown@example.test"})
    assert known.json()==unknown.json()=={"ok":True}
    code=latest_code(db_factory)
    values={"code":code,"password":"new-test-only-passphrase"}
    assert client.post("/api/v1/auth/reset-password",json=values).status_code==200
    assert client.post("/api/v1/auth/reset-password",json=values).status_code==400
    assert client.get("/api/v1/auth/me",headers=auth_headers).status_code==401
    assert client.post("/api/v1/auth/login",json={"email":"owner@example.com","password":"a-strong-passphrase"}).status_code==401
    assert client.post("/api/v1/auth/login",json={"email":"owner@example.com","password":values["password"]}).status_code==200


def test_expired_reset_does_not_change_the_password(client,auth_headers,db_factory):
    client.post("/api/v1/auth/password-reset",json={"email":"owner@example.com"})
    code=latest_code(db_factory)
    with db_factory() as db:
        db.scalar(select(AccountToken)).expires_at=utcnow()-timedelta(seconds=1)
        db.commit()
    assert client.post("/api/v1/auth/reset-password",json={"code":code,"password":"new-test-only-passphrase"}).status_code==400
    assert client.get("/api/v1/auth/me",headers=auth_headers).status_code==200


def test_account_mail_is_encrypted_deduplicated_and_delivered_locally(client,auth_headers,db_factory,monkeypatch):
    for _ in range(3):
        client.post("/api/v1/auth/request-verification",headers=auth_headers)
    with db_factory() as db:
        tickets=list(db.scalars(select(AccountToken)))
        assert len(tickets)==1
        token=account_mail.decrypt_token(tickets[0].encrypted_token)
        assert token not in tickets[0].encrypted_token and token!=tickets[0].token_hash
    messages=[]
    monkeypatch.setattr(settings,"mail_delivery_mode","preview")
    monkeypatch.setattr(account_mail,"send_message",lambda message:messages.append(message))
    assert account_mail.deliver_pending(db_factory)==1
    assert account_mail.deliver_pending(db_factory)==0
    assert "/confirmar-correo?codigo=" in messages[0].get_content()


def test_verification_and_reset_codes_are_not_interchangeable(client,auth_headers,db_factory):
    client.post("/api/v1/auth/request-verification",headers=auth_headers)
    assert client.post("/api/v1/auth/reset-password",json={"code":latest_code(db_factory),"password":"new-test-only-passphrase"}).status_code==400
