"""Property 27: Login failures do not disclose which field was wrong.

**Validates: Requirements 15.3**
"""

import uuid
from typing import Any

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from flask_app.auth.service import MAX_FAILED_LOGINS, register_service

passwords = st.text(
    alphabet=st.characters(blacklist_categories=["Cs", "Cc"]),
    min_size=8,
    max_size=40,
)
local_parts = st.from_regex(r"[a-z][a-z0-9]{2,15}", fullmatch=True)


def _login(client: Any, email: str, password: str) -> tuple[int, Any, list[str]]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return response.status_code, response.get_json(), response.headers.getlist("Set-Cookie")


# Feature: task-management-app, Property 27: Login failures do not disclose which field was wrong
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(local=local_parts, password=passwords, wrong=passwords, unknown_password=passwords)
def test_login_failures_are_identical_for_every_cause(
    client: Any, local: str, password: str, wrong: str, unknown_password: str
) -> None:
    assume(wrong != password)
    # Skip random passwords that coincidentally appear in the fixed generic message
    # (e.g. "authenti"), which would be a false positive for the leak check.
    _, baseline_body, _ = _login(client, "baseline-unknown@example.com", "Baseline-pw-1")
    baseline = str(baseline_body).lower()
    assume(password.lower() not in baseline and wrong.lower() not in baseline)
    suffix = uuid.uuid4().hex[:8]
    email = f"{local}-{suffix}@example.com"
    unknown_email = f"nobody-{local}-{suffix}@example.com"
    register_service({"email": email, "password": password, "display_name": "Prop User"})

    failures = [("unknown email", _login(client, unknown_email, unknown_password))]
    failures.append(("wrong password", _login(client, email, wrong)))
    for _ in range(MAX_FAILED_LOGINS - 1):
        _login(client, email, wrong)  # reach the lockout threshold
    failures.append(("locked, wrong password", _login(client, email, wrong)))
    failures.append(("locked, correct password", _login(client, email, password)))

    reference_status, reference_body, _ = failures[0][1]
    assert reference_status == 401
    assert set(reference_body) == {"error"}
    for cause, (status, body, cookies) in failures:
        assert status == reference_status, cause
        assert body == reference_body, cause
        assert cookies == [], cause
        text = str(body).lower()
        for secret in (email, password, wrong, "argon2", "token", "lock"):
            assert secret.lower() not in text, cause
