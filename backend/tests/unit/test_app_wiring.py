import logging
from typing import Any

import pytest

from flask_app.models import InvitationLink, User
from scripts.seed import INVITATION_TOKEN, seed_data


def test_request_log_uses_route_template_only(
    client: Any, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "SECRETTOKEN123"
    with caplog.at_level(logging.INFO):
        client.get(f"/api/guest/{secret}/board?q=hidden", headers={"Cookie": "access_token=abc"})
        client.get("/no/such/path-with-secret")
    text = caplog.text
    assert "GET /api/guest/<token>/board -> 403 user=-" in text
    assert "GET unmatched -> 404 user=-" in text
    for forbidden in (secret, "hidden", "abc", "path-with-secret"):
        assert forbidden not in text


def test_seed_is_idempotent(db_session: Any) -> None:
    first = seed_data()
    users = db_session.query(User).count()
    second = seed_data()
    assert first == second
    assert db_session.query(User).count() == users
    links = db_session.query(InvitationLink).filter_by(token=INVITATION_TOKEN).count()
    assert links == 1
