"""Property 40: Profile updates validate the display name and password changes
require the current password.

**Validates: Requirements 18.2, 18.3, 18.4, 18.6, 18.7, 18.8, 18.9**
"""

import uuid
from typing import Any

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.auth.schema import ChangePasswordSchema, UpdateProfileSchema
from flask_app.auth.service import (
    MAX_FAILED_LOGINS,
    change_password_service,
    login_service,
    register_service,
    update_profile_service,
)
from flask_app.common.exceptions import ValidationError
from flask_app.common.validation import load_schema
from flask_app.extensions import db
from flask_app.models import RefreshToken, User
from tests.conftest import FakeClock

passwords = st.text(
    alphabet=st.characters(blacklist_categories=["Cs", "Cc"]),
    min_size=8,
    max_size=24,
)
short_passwords = st.text(
    alphabet=st.characters(blacklist_categories=["Cs", "Cc"]),
    min_size=0,
    max_size=7,
)
local_parts = st.from_regex(r"[a-z][a-z0-9]{2,15}", fullmatch=True)
_NAME_CHARS = st.characters(blacklist_categories=["Cs", "Cc", "Z"])
core_names = st.text(alphabet=_NAME_CHARS, min_size=1, max_size=50)
padding = st.text(alphabet=" \t", max_size=5)
blank_names = st.text(alphabet=" \t\n", max_size=60)
long_names = st.text(alphabet=_NAME_CHARS, min_size=51, max_size=80)

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


def _register(local: str, password: str) -> User:
    email = f"{local}-{uuid.uuid4().hex[:8]}@example.com"
    register_service({"email": email, "password": password, "display_name": "Prop"})
    user: User | None = db.session.scalar(select(User).where(User.email == email))
    assert user is not None
    return user


def _active_tokens(user: User) -> int:
    return len(
        db.session.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False)
            )
        ).all()
    )


def _change(user: User, current: str, new: str) -> Any:
    payload = load_schema(
        ChangePasswordSchema(), {"current_password": current, "new_password": new}
    )
    return change_password_service(user, payload)


# Feature: task-management-app, Property 40: Profile updates validate the display name and password changes require the current password  # noqa: E501
@_SETTINGS
@given(
    local=local_parts,
    password=passwords,
    name=core_names,
    left=padding,
    right=padding,
)
def test_valid_display_name_is_trimmed_and_stored(
    db_session: Any, clock: FakeClock, local: str, password: str, name: str, left: str, right: str
) -> None:
    user = _register(local, password)
    payload = load_schema(UpdateProfileSchema(), {"display_name": f"{left}{name}{right}"})
    identity = update_profile_service(user, payload)
    assert identity["display_name"] == name.strip()
    assert user.display_name == name.strip()
    assert 1 <= len(user.display_name) <= 50


# Feature: task-management-app, Property 40: Profile updates validate the display name and password changes require the current password  # noqa: E501
@_SETTINGS
@given(bad=st.one_of(blank_names, long_names), extra=st.sampled_from(["email", "password"]))
def test_invalid_display_name_and_extra_keys_are_rejected(bad: str, extra: str) -> None:
    with pytest.raises(ValidationError) as caught:
        load_schema(UpdateProfileSchema(), {"display_name": bad})
    assert caught.value.field == "display_name"

    with pytest.raises(ValidationError):
        load_schema(UpdateProfileSchema(), {"display_name": "Valid", extra: "x@example.com"})


# Feature: task-management-app, Property 40: Profile updates validate the display name and password changes require the current password  # noqa: E501
@_SETTINGS
@given(local=local_parts, password=passwords, new=passwords)
def test_correct_current_password_changes_hash_revokes_tokens_resets_lockout(
    db_session: Any, clock: FakeClock, local: str, password: str, new: str
) -> None:
    assume(new != password)
    user = _register(local, password)
    login_service({"email": user.email, "password": password})
    login_service({"email": user.email, "password": password})
    user.failed_login_attempts = MAX_FAILED_LOGINS - 1
    db.session.commit()
    old_hash = user.password_hash
    old_tokens = set(
        db.session.scalars(select(RefreshToken.id).where(RefreshToken.user_id == user.id)).all()
    )
    assert _active_tokens(user) == 2

    identity, access, refresh = _change(user, password, new)

    assert identity["email"] == user.email
    assert access
    assert refresh
    assert user.password_hash != old_hash
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    # Every earlier token is revoked; only the new session's token is active.
    assert _active_tokens(user) == 1
    for token in db.session.scalars(
        select(RefreshToken).where(RefreshToken.id.in_(old_tokens))
    ).all():
        assert token.revoked
    # The new password works, the old one does not.
    login_service({"email": user.email, "password": new})


# Feature: task-management-app, Property 40: Profile updates validate the display name and password changes require the current password  # noqa: E501
@_SETTINGS
@given(
    local=local_parts,
    password=passwords,
    wrong=passwords,
    new=passwords,
    attempts=st.integers(min_value=1, max_value=MAX_FAILED_LOGINS),
)
def test_wrong_current_password_is_rejected_counts_toward_lockout_and_locks(
    db_session: Any,
    clock: FakeClock,
    local: str,
    password: str,
    wrong: str,
    new: str,
    attempts: int,
) -> None:
    assume(wrong != password)
    user = _register(local, password)
    old_hash = user.password_hash

    messages = []
    for i in range(attempts):
        with pytest.raises(ValidationError) as caught:
            _change(user, wrong, new)
        assert caught.value.field == "current_password"
        messages.append(str(caught.value))
        assert user.failed_login_attempts == i + 1
    assert user.password_hash == old_hash

    if attempts == MAX_FAILED_LOGINS:
        assert user.locked_until is not None
        # Locked: the correct password gets the same error and changes nothing.
        with pytest.raises(ValidationError) as caught:
            _change(user, password, new)
        assert str(caught.value) == messages[0]
        assert caught.value.field == "current_password"
        assert user.password_hash == old_hash
        assert user.failed_login_attempts == MAX_FAILED_LOGINS
    else:
        assert user.locked_until is None


# Feature: task-management-app, Property 40: Profile updates validate the display name and password changes require the current password  # noqa: E501
@_SETTINGS
@given(local=local_parts, password=passwords, short=short_passwords)
def test_short_or_unchanged_new_password_is_rejected_without_counting_failure(
    db_session: Any, clock: FakeClock, local: str, password: str, short: str
) -> None:
    user = _register(local, password)
    old_hash = user.password_hash

    with pytest.raises(ValidationError) as caught:
        _change(user, password, short)
    assert caught.value.field == "new_password"

    with pytest.raises(ValidationError) as caught:
        _change(user, password, password)
    assert caught.value.field == "new_password"

    assert user.password_hash == old_hash
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
