"""Property 28: Registration validation enforces email format, password length,
uniqueness, and display name.

**Validates: Requirements 15.14, 15.15, 15.16**
"""

import uuid
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select

from flask_app.models import User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_text = st.characters(blacklist_categories=["Cs", "Cc"])
valid_passwords = st.text(alphabet=_text, min_size=8, max_size=40)
short_passwords = st.text(alphabet=_text, min_size=0, max_size=7)
core_names = st.from_regex(r"[A-Za-z0-9]{1,50}", fullmatch=True)
padding = st.text(alphabet=" \t", max_size=5)
blank_names = st.text(alphabet=" \t\n", max_size=60)
long_names = st.from_regex(r"[A-Za-z0-9]{51,80}", fullmatch=True)
invalid_emails = st.one_of(
    st.text(alphabet=st.characters(blacklist_categories=["Cs", "Cc"], blacklist_characters="@")),
    st.from_regex(r"[a-z]{1,8}@", fullmatch=True),
    st.from_regex(r"@[a-z]{1,8}\.com", fullmatch=True),
    st.from_regex(r"[a-z]{1,8}@@[a-z]{1,8}\.com", fullmatch=True),
    st.from_regex(r"[a-z]{1,8} [a-z]{1,8}@example\.com", fullmatch=True),
)


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def _register(client: Any, email: str, password: str, display_name: str) -> Any:
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "displayName": display_name},
    )


def _user_count(db_session: Any) -> int:
    return int(db_session.scalar(select(func.count()).select_from(User)))


def _assert_rejected(response: Any, before: int, db_session: Any, field: str | None) -> None:
    assert response.status_code == 400
    body = response.get_json()
    assert set(body) == {"error"}
    if field is not None:
        assert body["error"].get("field") == field
    assert _user_count(db_session) == before


# Feature: task-management-app, Property 28: Registration validation enforces email format, password length, uniqueness, and display name  # noqa: E501
@_SETTINGS
@given(email=invalid_emails, password=valid_passwords, name=core_names)
def test_invalid_email_format_is_rejected(
    client: Any, db_session: Any, email: str, password: str, name: str
) -> None:
    before = _user_count(db_session)
    _assert_rejected(_register(client, email, password, name), before, db_session, "email")


# Feature: task-management-app, Property 28: Registration validation enforces email format, password length, uniqueness, and display name  # noqa: E501
@_SETTINGS
@given(password=short_passwords, name=core_names)
def test_short_password_is_rejected(client: Any, db_session: Any, password: str, name: str) -> None:
    before = _user_count(db_session)
    response = _register(client, _email(), password, name)
    _assert_rejected(response, before, db_session, "password")


# Feature: task-management-app, Property 28: Registration validation enforces email format, password length, uniqueness, and display name  # noqa: E501
@_SETTINGS
@given(name=st.one_of(blank_names, long_names), password=valid_passwords)
def test_blank_or_overlong_display_name_is_rejected(
    client: Any, db_session: Any, name: str, password: str
) -> None:
    before = _user_count(db_session)
    response = _register(client, _email(), password, name)
    _assert_rejected(response, before, db_session, "displayName")


# Feature: task-management-app, Property 28: Registration validation enforces email format, password length, uniqueness, and display name  # noqa: E501
@_SETTINGS
@given(
    password=valid_passwords,
    name=core_names,
    case_mask=st.lists(st.booleans(), min_size=40, max_size=40),
)
def test_duplicate_email_is_rejected_case_insensitively(
    client: Any, db_session: Any, password: str, name: str, case_mask: list[bool]
) -> None:
    email = _email()
    assert _register(client, email, password, name).status_code == 201
    before = _user_count(db_session)
    variant = "".join(c.upper() if upper else c for c, upper in zip(email, case_mask, strict=False))
    response = _register(client, variant, password, name)
    _assert_rejected(response, before, db_session, "email")


# Feature: task-management-app, Property 28: Registration validation enforces email format, password length, uniqueness, and display name  # noqa: E501
@_SETTINGS
@given(password=valid_passwords, name=core_names, left=padding, right=padding)
def test_valid_registration_succeeds_with_trimmed_name(
    client: Any, db_session: Any, password: str, name: str, left: str, right: str
) -> None:
    email = _email()
    before = _user_count(db_session)
    response = _register(client, email, password, f"{left}{name}{right}")
    assert response.status_code == 201
    assert _user_count(db_session) == before + 1
    user = db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    assert user.display_name == name


# Feature: task-management-app, Property 28: Registration validation enforces email format, password length, uniqueness, and display name  # noqa: E501
@_SETTINGS
@given(
    core=st.text(alphabet=" ab", min_size=8, max_size=12),
    name=core_names,
)
def test_password_is_never_trimmed(client: Any, db_session: Any, core: str, name: str) -> None:
    """Whitespace counts toward the 8-character minimum."""
    response = _register(client, _email(), core, name)
    assert response.status_code == 201
