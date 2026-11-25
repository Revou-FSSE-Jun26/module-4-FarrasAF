"""Authentication_Service: registration, login, refresh, logout, identity."""

import hashlib
import secrets
import uuid
from datetime import timedelta
from functools import cache
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from flask import current_app
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from flask_app.common.exceptions import AuthenticationError, ValidationError
from flask_app.common.time import utc_now
from flask_app.extensions import db
from flask_app.models import RefreshToken, User

MAX_FAILED_LOGINS = 3
LOCKOUT_MINUTES = 15
_JWT_ALGORITHM = "HS256"
_GENERIC_LOGIN_ERROR = "Invalid email or password"
_INVALID_SESSION = "Authentication required"

_hasher = PasswordHasher()


@cache
def _dummy_hash() -> str:
    """Hash verified for unknown emails so response time does not reveal them."""
    return _hasher.hash("dummy-password-for-timing")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError, InvalidHashError:
        return False


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def user_identity(user: User) -> dict[str, Any]:
    return {"id": user.id, "email": user.email, "display_name": user.display_name}


def create_access_token(user_id: uuid.UUID) -> str:
    now = utc_now()
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=current_app.config["ACCESS_TOKEN_MINUTES"]),
    }
    return jwt.encode(claims, current_app.config["JWT_SECRET_KEY"], algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    """Return the user id from a valid access token or raise AuthenticationError."""
    try:
        claims = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=[_JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return uuid.UUID(str(claims["sub"]))
    except (jwt.PyJWTError, ValueError) as exc:
        raise AuthenticationError(_INVALID_SESSION) from exc


def _issue_refresh_token(user: User) -> str:
    raw = secrets.token_urlsafe(48)
    expires_at = utc_now() + timedelta(days=current_app.config["REFRESH_TOKEN_DAYS"])
    db.session.add(
        RefreshToken(user_id=user.id, token_hash=hash_refresh_token(raw), expires_at=expires_at)
    )
    return raw


def register_service(payload: dict[str, Any]) -> dict[str, Any]:
    """Create an account only; no tokens are issued."""
    email = _normalize_email(payload["email"])
    duplicate = ValidationError("Email is already registered", field="email")
    if db.session.scalar(select(User.id).where(User.email == email)) is not None:
        raise duplicate
    user = User(
        email=email,
        password_hash=_hasher.hash(payload["password"]),
        display_name=payload["display_name"],
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise duplicate from exc
    return user_identity(user)


def login_service(payload: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    """Verify credentials with lockout; return (identity, access_token, refresh_token)."""
    email = _normalize_email(payload["email"])
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None:
        _verify_password(_dummy_hash(), payload["password"])
        raise AuthenticationError(_GENERIC_LOGIN_ERROR)
    now = utc_now()
    if user.locked_until is not None:
        if user.locked_until > now:
            raise AuthenticationError(_GENERIC_LOGIN_ERROR)
        user.locked_until = None
        user.failed_login_attempts = 0
    if not _verify_password(user.password_hash, payload["password"]):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
        db.session.commit()  # persist the counter; the error handler rolls back
        raise AuthenticationError(_GENERIC_LOGIN_ERROR)
    user.failed_login_attempts = 0
    user.locked_until = None
    refresh_token = _issue_refresh_token(user)
    access_token = create_access_token(user.id)
    db.session.commit()
    return user_identity(user), access_token, refresh_token


def _find_valid_refresh_token(raw: str | None) -> RefreshToken | None:
    if not raw:
        return None
    token: RefreshToken | None = db.session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw))
    )
    if token is None or token.revoked or token.expires_at <= utc_now():
        return None
    return token


def refresh_service(raw_refresh_token: str | None) -> tuple[dict[str, Any], str]:
    """Return (identity, new access_token) for a valid refresh token."""
    token = _find_valid_refresh_token(raw_refresh_token)
    if token is None:
        raise AuthenticationError(_INVALID_SESSION)
    user = get_user_by_id(token.user_id)
    return user_identity(user), create_access_token(user.id)


def logout_service(raw_refresh_token: str | None) -> None:
    """Revoke the presented refresh token; unknown or missing tokens are a no-op."""
    token = _find_valid_refresh_token(raw_refresh_token)
    if token is not None:
        token.revoked = True
        db.session.commit()


def get_user_by_id(user_id: uuid.UUID) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        raise AuthenticationError(_INVALID_SESSION)
    return user


def me_service(user: User) -> dict[str, Any]:
    return user_identity(user)


def update_profile_service(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    """Update the display name (the only editable profile field)."""
    if "display_name" in payload:
        user.display_name = payload["display_name"]
        user.updated_at = utc_now()
    db.session.commit()
    return user_identity(user)


def change_password_service(user: User, payload: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    """Change the password, revoke all refresh tokens, and start a new session.

    Returns (identity, access_token, refresh_token) for the route to set as cookies.
    """
    wrong = ValidationError("Current password is incorrect", field="current_password")
    now = utc_now()
    if user.locked_until is not None:
        if user.locked_until > now:
            raise wrong
        user.locked_until = None
        user.failed_login_attempts = 0
    if not _verify_password(user.password_hash, payload["current_password"]):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
        db.session.commit()  # persist the counter even though the request fails
        raise wrong
    if payload["new_password"] == payload["current_password"]:
        raise ValidationError(
            "New password must differ from the current password", field="new_password"
        )
    user.password_hash = _hasher.hash(payload["new_password"])
    user.failed_login_attempts = 0
    user.locked_until = None
    user.updated_at = now
    db.session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    refresh_token = _issue_refresh_token(user)
    access_token = create_access_token(user.id)
    db.session.commit()
    return user_identity(user), access_token, refresh_token
