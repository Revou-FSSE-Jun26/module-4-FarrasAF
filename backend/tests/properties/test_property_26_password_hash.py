"""Property 26: Passwords are stored as a verifiable argon2 hash.

**Validates: Requirements 15.1**
"""

import uuid
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.auth.service import register_service
from flask_app.models import User

# Passwords are never trimmed, so leading/trailing whitespace is kept.
passwords = st.text(
    alphabet=st.characters(blacklist_categories=["Cs"]),
    min_size=1,
    max_size=64,
)

_verifier = PasswordHasher()


def _matches(password_hash: str, password: str) -> bool:
    try:
        return _verifier.verify(password_hash, password)
    except VerifyMismatchError:
        return False


# Feature: task-management-app, Property 26: Passwords are stored as a verifiable argon2 hash
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(password=passwords, other=passwords)
def test_registered_password_is_stored_as_verifiable_argon2_hash(
    db_session: Any, password: str, other: str
) -> None:
    assume(other != password)
    email = f"user-{uuid.uuid4().hex}@example.com"

    identity = register_service({"email": email, "password": password, "display_name": "Prop User"})

    stored = db_session.scalar(select(User.password_hash).where(User.id == identity["id"]))
    assert stored.startswith("$argon2")
    assert stored != password
    assert _matches(stored, password)
    assert not _matches(stored, other)
    assert not _matches(stored, password + " ")
