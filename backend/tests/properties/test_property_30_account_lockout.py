"""Property 30: Account lockout after three consecutive failed logins.

**Validates: Requirements 15.4, 15.5, 15.6, 15.7**
"""

import uuid
from datetime import timedelta
from typing import Any

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.auth.service import (
    LOCKOUT_MINUTES,
    MAX_FAILED_LOGINS,
    login_service,
    register_service,
)
from flask_app.common.exceptions import AuthenticationError
from flask_app.extensions import db
from flask_app.models import User
from tests.conftest import FakeClock

passwords = st.text(
    alphabet=st.characters(blacklist_categories=["Cs", "Cc"]),
    min_size=8,
    max_size=40,
)
local_parts = st.from_regex(r"[a-z][a-z0-9]{2,15}", fullmatch=True)

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


def _register(local: str, password: str) -> str:
    email = f"{local}-{uuid.uuid4().hex[:8]}@example.com"
    register_service({"email": email, "password": password, "display_name": "Prop"})
    return email


def _user(email: str) -> User:
    user: User | None = db.session.scalar(select(User).where(User.email == email))
    assert user is not None
    return user


def _fail(email: str, wrong: str) -> str:
    with pytest.raises(AuthenticationError) as caught:
        login_service({"email": email, "password": wrong})
    return str(caught.value)


# Feature: task-management-app, Property 30: Account lockout after three consecutive failed logins
@_SETTINGS
@given(
    local=local_parts,
    password=passwords,
    wrong=passwords,
    elapsed_seconds=st.integers(min_value=0, max_value=LOCKOUT_MINUTES * 60 - 1),
)
def test_three_failures_lock_account_and_reject_correct_credentials(
    db_session: Any,
    clock: FakeClock,
    local: str,
    password: str,
    wrong: str,
    elapsed_seconds: int,
) -> None:
    assume(wrong != password)
    email = _register(local, password)
    locked_at = clock.now

    messages = [_fail(email, wrong) for _ in range(MAX_FAILED_LOGINS)]

    user = _user(email)
    assert user.failed_login_attempts == MAX_FAILED_LOGINS
    assert user.locked_until == locked_at + timedelta(minutes=LOCKOUT_MINUTES)

    clock.advance(seconds=elapsed_seconds)
    # While locked, correct and wrong credentials give the same generic error.
    assert _fail(email, password) == messages[0]
    assert _fail(email, wrong) == messages[0]
    assert len(set(messages)) == 1


# Feature: task-management-app, Property 30: Account lockout after three consecutive failed logins
@_SETTINGS
@given(
    local=local_parts,
    password=passwords,
    wrong=passwords,
    failures=st.integers(min_value=0, max_value=MAX_FAILED_LOGINS - 1),
)
def test_success_before_threshold_resets_counter(
    db_session: Any, clock: FakeClock, local: str, password: str, wrong: str, failures: int
) -> None:
    assume(wrong != password)
    email = _register(local, password)

    for _ in range(failures):
        _fail(email, wrong)
    assert _user(email).failed_login_attempts == failures
    assert _user(email).locked_until is None

    login_service({"email": email, "password": password})
    assert _user(email).failed_login_attempts == 0

    # The counter restarted: fewer than the threshold failures still do not lock.
    for _ in range(MAX_FAILED_LOGINS - 1):
        _fail(email, wrong)
    assert _user(email).locked_until is None
    login_service({"email": email, "password": password})


# Feature: task-management-app, Property 30: Account lockout after three consecutive failed logins
@_SETTINGS
@given(
    local=local_parts,
    password=passwords,
    wrong=passwords,
    extra_seconds=st.integers(min_value=0, max_value=7 * 24 * 3600),
)
def test_login_succeeds_after_lockout_elapses_and_counter_resets(
    db_session: Any, clock: FakeClock, local: str, password: str, wrong: str, extra_seconds: int
) -> None:
    assume(wrong != password)
    email = _register(local, password)
    for _ in range(MAX_FAILED_LOGINS):
        _fail(email, wrong)

    clock.advance(minutes=LOCKOUT_MINUTES, seconds=extra_seconds)

    identity, access, refresh = login_service({"email": email, "password": password})
    assert identity["email"] == email
    assert access
    assert refresh
    user = _user(email)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
