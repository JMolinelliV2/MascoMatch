import base64
import hashlib
from datetime import timedelta
from uuid import UUID
import pytest
from pydantic import ValidationError, SecretStr
from app.analysis.service import utcnow
from app.core.config import Settings, settings
from app.core.rate_limit import client_address, private_key
from app.models import AuthSession, User


def test_logout_revokes_the_token_but_keeps_other_device_session(client, auth_headers):
    second = client.post("/api/v1/auth/login", json={"email":"owner@example.com", "password":"a-strong-passphrase"}).json()
    other = {"Authorization": "Bearer " + second["access_token"]}
    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401
    assert client.get("/api/v1/auth/me", headers=other).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 401


def test_database_session_expiry_is_checked(client, auth_headers, db_factory):
    from app.core.security import decode_token_claims
    claims = decode_token_claims(auth_headers["Authorization"][7:])
    with db_factory() as db:
        db.get(AuthSession, UUID(claims["jti"])).expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401


def test_existing_password_hash_is_upgraded_at_login(client, auth_headers, db_factory):
    salt = b"existing-example"
    digest = hashlib.pbkdf2_hmac("sha256", b"a-strong-passphrase", salt, 310000)
    with db_factory() as db:
        from sqlalchemy import select
        user = db.scalar(select(User))
        user.password_hash = "pbkdf2_sha256$310000$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()
        identity = user.id
        db.commit()
    assert client.post("/api/v1/auth/login", json={"email":"owner@example.com", "password":"a-strong-passphrase"}).status_code == 200
    with db_factory() as db:
        assert db.get(User, identity).password_hash.startswith("pbkdf2_sha256$600000$")


def production_values():
    return dict(app_env="production", jwt_secret="a"*48, s3_secret_key="b"*48,
                metrics_token="c"*48, database_url="postgresql+psycopg://app:secret@db/mascomatch",
                rate_limit_backend="redis", web_origin="https://mascomatch.com", public_site_url="https://mascomatch.com")


@pytest.mark.parametrize("override", [
    {"jwt_secret":"replace-with-a-long-random-secret"}, {"rate_limit_backend":"memory"},
    {"rate_limit_enabled":False}, {"public_site_url":"http://mascomatch.com"},
    {"web_origin":"*"}, {"trusted_proxy_ips":"0.0.0.0/0"}, {"allowed_hosts":"*"},
    {"metrics_token":"short"}, {"mail_delivery_mode":"preview"}, {"database_url":"sqlite://"},
])
def test_unsafe_production_settings_fail_closed(override):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**production_values(), **override})


def test_secret_files_are_supported_and_not_in_repr(tmp_path, monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    key = tmp_path / "jwt_secret"
    key.write_text("private-example-" + "a"*40)
    config = Settings(_env_file=None, jwt_secret_file=str(key))
    assert config.jwt_secret == key.read_text()
    assert config.jwt_secret not in repr(config)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret_file=str(key), jwt_secret="ambiguous")


def test_only_known_proxy_addresses_can_supply_client_ip(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_ips", "172.30.50.2,172.30.50.3")
    def scope(peer, header):
        return {"client":(peer,1234), "headers":[(b"x-mascomatch-client-ip",header)]}
    assert client_address(scope("172.30.50.2", b"198.51.100.10")) == "198.51.100.10"
    assert client_address(scope("198.51.100.20", b"198.51.100.10")) == "198.51.100.20"
    assert client_address(scope("172.30.50.2", b"malformed")) == "172.30.50.2"
    assert "owner@example.test" not in private_key("auth", "owner@example.test")


def test_operational_metrics_require_private_token(client, monkeypatch):
    monkeypatch.setattr(settings, "metrics_token", SecretStr("private-monitoring-"+"x"*32))
    monkeypatch.setattr("app.routers.operations.readiness", lambda:{"database":True,"queue":True,"photos":True})
    assert client.get("/internal/metrics").status_code == 404
    assert client.get("/internal/metrics", headers={"Authorization":"Bearer wrong"}).status_code == 404
    assert client.get("/health/ready").status_code == 200
    monkeypatch.setattr("app.routers.operations.readiness", lambda:{"database":False})
    assert client.get("/health/ready").status_code == 503


def test_untrusted_host_is_rejected(client):
    assert client.get("/health", headers={"Host":"untrusted.example"}).status_code == 400
