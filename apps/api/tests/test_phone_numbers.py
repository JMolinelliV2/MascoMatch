import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.found_reports import FinderContactCreate
from app.models import User
from app.phone_numbers import optional_phone, validate_phone
from app.routers.auth import ContactUpdate
from app.schemas import RegisterRequest

VALID = [
    "099 123 456", "99 123 456", "098765432", "2400 1234",
    "+598 99 123 456", "+598 98 765 432", "+598 2400 1234",
    "00598 99 123 456", "+54 9 11 2345 6789", "+55 11 91234-5678",
    "+44 20 8366 1177", "+34 612 34 56 78", "+1 (202) 555-0123",
]
INVALID = [
    "8812391923012301023", "11111111", "00000000", "09912345", "0991234567",
    "+598 11111111", "+598 123", "+999 99123456", "+1 200 123 0101",
    "abc", "099123456abc", "Llamar al +59899123456", "+59899123456 ext 123",
    "+598+99123456", "０９９１２３４５６", "12345678901234567890123456789012345",
]


@pytest.mark.parametrize("phone", VALID)
def test_valid_phones_work_in_every_input_schema(phone):
    assert validate_phone(phone) == phone
    assert FinderContactCreate(name="Persona de prueba", phone=phone).phone == phone
    assert RegisterRequest(email="phone@example.test", password="test-only-passphrase", name="Test", phone=phone).phone == phone
    assert ContactUpdate(email="phone@example.test", name="Test", phone=phone).phone == phone


@pytest.mark.parametrize("phone", INVALID)
def test_invalid_phones_are_rejected_by_every_input_schema(phone):
    with pytest.raises(ValueError):
        validate_phone(phone)
    for schema, fields in [
        (FinderContactCreate, {"name": "Persona de prueba"}),
        (RegisterRequest, {"email": "phone@example.test", "password": "test-only-passphrase", "name": "Test"}),
        (ContactUpdate, {"email": "phone@example.test", "name": "Test"}),
    ]:
        with pytest.raises(ValidationError):
            schema(phone=phone, **fields)


def test_optional_phone_can_be_omitted_or_cleared_and_valid_spaces_are_trimmed():
    for value in [None, "", "   "]:
        assert optional_phone(value) is None
        assert ContactUpdate(email="phone@example.test", name="Test", phone=value).phone is None
    assert validate_phone("  +598 99 123 456  ") == "+598 99 123 456"


def test_registration_rejects_an_impossible_phone_before_creating_an_account(client, db_factory):
    response = client.post("/api/v1/auth/register", json={"email": "phone@example.test",
        "password": "test-only-passphrase", "name": "Test", "phone": INVALID[0]})
    assert response.status_code == 422
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 0


def test_contact_update_rejects_invalid_phone_without_saving_other_changes(client, auth_headers):
    original = client.get("/api/v1/auth/me", headers=auth_headers).json()
    for phone in INVALID[:9]:
        response = client.patch("/api/v1/auth/contact", headers=auth_headers,
            json={"name": "Unwanted name change", "email": original["email"], "phone": phone})
        assert response.status_code == 422
        current = client.get("/api/v1/auth/me", headers=auth_headers).json()
        assert (current["name"], current["phone"]) == (original["name"], original["phone"])
    data = {"name": original["name"], "email": original["email"], "phone": "099 123 456"}
    assert client.patch("/api/v1/auth/contact", headers=auth_headers, json=data).json()["phone"] == data["phone"]
    data["phone"] = " "
    response = client.patch("/api/v1/auth/contact", headers=auth_headers, json=data)
    assert response.status_code == 200 and response.json()["phone"] is None


def test_registration_accepts_a_valid_phone(client):
    response = client.post("/api/v1/auth/register", json={"email": "phone@example.test",
        "password": "test-only-passphrase", "name": "Test", "phone": "+598 99 123 456"})
    assert response.status_code == 201
    assert response.json()["user"]["phone"] == "+598 99 123 456"
