"""Property 21: RBAC authorization decisions match the role capability matrix.

**Validates: Requirements 1.7, 2.8, 3.6, 4.6, 5.6, 8.14, 10.7, 11.4, 11.7, 12.1-12.5**
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from flask_app.access.rbac import role_allows

# Independent expected matrix, written from the requirements (not imported from rbac.py).
_GUEST_OPS = {"read_board_content"}
_MEMBER_OPS = _GUEST_OPS | {
    "card_write",
    "comment_write",
    "activity_search_notifications_analytics",
}
_ADMIN_OPS = _MEMBER_OPS | {"column_manage", "board_admin"}
_EXPECTED: dict[str, set[str]] = {
    "guest": _GUEST_OPS,
    "member": _MEMBER_OPS,
    "admin": _ADMIN_OPS,
}
_ALL_OPS = sorted(_ADMIN_OPS)

roles = st.sampled_from(["guest", "member", "admin"])
operations = st.sampled_from(_ALL_OPS)
unknown_roles = st.text(max_size=12).filter(lambda r: r not in _EXPECTED)


# Feature: task-management-app, Property 21: RBAC authorization decisions match the role capability matrix  # noqa: E501
@settings(max_examples=200)
@given(role=roles, operation=operations)
def test_known_role_decision_matches_matrix(role: str, operation: str) -> None:
    assert role_allows(role, operation) is (operation in _EXPECTED[role])


# Feature: task-management-app, Property 21: RBAC authorization decisions match the role capability matrix  # noqa: E501
@settings(max_examples=100)
@given(operation=st.one_of(operations, st.text(max_size=20)))
def test_no_role_is_always_denied(operation: str) -> None:
    assert role_allows(None, operation) is False


# Feature: task-management-app, Property 21: RBAC authorization decisions match the role capability matrix  # noqa: E501
@settings(max_examples=100)
@given(role=unknown_roles, operation=operations)
def test_unknown_role_is_denied(role: str, operation: str) -> None:
    assert role_allows(role, operation) is False


# Feature: task-management-app, Property 21: RBAC authorization decisions match the role capability matrix  # noqa: E501
@settings(max_examples=100)
@given(role=roles, operation=st.text(max_size=20).filter(lambda o: o not in _ALL_OPS))
def test_unknown_operation_is_denied(role: str, operation: str) -> None:
    assert role_allows(role, operation) is False
