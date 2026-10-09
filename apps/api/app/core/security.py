import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config import settings

ALGORITHM = "HS256"
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        if not 100_000 <= int(iterations) <= 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, OverflowError):
        return False


def password_needs_upgrade(encoded: str) -> bool:
    try:
        return int(encoded.split("$")[1]) < PBKDF2_ITERATIONS
    except (IndexError, ValueError):
        return True


def create_access_token(user_id: UUID, session_id: UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes),
               "iss": "mascomatch", "aud": "mascomatch-api", "type": "access"}
    payload["jti"] = str(session_id)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> UUID:
    return UUID(decode_token_claims(token)["sub"])


def decode_token_claims(token: str) -> dict:
    if len(token) > 4096:
        raise jwt.InvalidTokenError("Invalid token length")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM],
                         issuer="mascomatch", audience="mascomatch-api",
                         options={"require": ["sub", "iat", "exp", "iss", "aud", "jti", "type"]})
    if payload["type"] != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    UUID(payload["sub"])
    UUID(payload["jti"])
    return payload

