import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app import models  # noqa: F401
from app.core.config import settings


@pytest.fixture()
def db_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    yield TestingSession
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(db_factory, monkeypatch):
    # No Redis or model request is started by the test application lifespan.
    monkeypatch.setattr(settings, "ai_enabled", False)

    def override_get_db():
        db = db_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    response = client.post("/api/v1/auth/register", json={"email": "owner@example.com", "password": "a-strong-passphrase", "name": "Owner"})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

