from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token_claims
from app.analysis.service import utcnow
from app.matching.linked import aware
from app.db.session import get_db
from app.models import User, AuthSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        claims = decode_token_claims(token)
        user_id = UUID(claims["sub"])
        session = db.get(AuthSession, UUID(claims["jti"]))
        if session is None or session.user_id != user_id or session.revoked_at is not None or aware(session.expires_at) <= utcnow():
            raise jwt.InvalidTokenError("Session unavailable")
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, user_id)
    if user is None or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is unavailable", headers={"WWW-Authenticate": "Bearer"})
    return user


def optional_user(token: str | None = Depends(optional_oauth2_scheme), db: Session = Depends(get_db)) -> User | None:
    return current_user(token, db) if token else None


