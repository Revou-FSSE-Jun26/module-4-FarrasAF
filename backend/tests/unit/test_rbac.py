import pytest

from flask_app.access.rbac import (
    ACTIVITY_SEARCH_NOTIFICATIONS_ANALYTICS,
    BOARD_ADMIN,
    CARD_WRITE,
    COLUMN_MANAGE,
    COMMENT_WRITE,
    READ_BOARD_CONTENT,
    role_allows,
)

WRITE_OPS = [CARD_WRITE, COMMENT_WRITE, ACTIVITY_SEARCH_NOTIFICATIONS_ANALYTICS]
ADMIN_OPS = [COLUMN_MANAGE, BOARD_ADMIN]


@pytest.mark.parametrize("op", [READ_BOARD_CONTENT, *WRITE_OPS, *ADMIN_OPS])
def test_no_role_is_denied_everything(op: str) -> None:
    assert not role_allows(None, op)
    assert not role_allows("unknown", op)


def test_guest_is_read_only() -> None:
    assert role_allows("guest", READ_BOARD_CONTENT)
    assert not any(role_allows("guest", op) for op in [*WRITE_OPS, *ADMIN_OPS])


def test_member_has_member_ops_but_not_admin_ops() -> None:
    assert all(role_allows("member", op) for op in [READ_BOARD_CONTENT, *WRITE_OPS])
    assert not any(role_allows("member", op) for op in ADMIN_OPS)


def test_admin_has_everything() -> None:
    assert all(role_allows("admin", op) for op in [READ_BOARD_CONTENT, *WRITE_OPS, *ADMIN_OPS])
