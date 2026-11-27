"""Role-based access control: the pure role decision and the @require_role decorator."""

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Literal

from flask_app.auth.decorators import current_user, token_required
from flask_app.common.exceptions import AuthorizationError, NotFoundError
from flask_app.extensions import db
from flask_app.models import BoardMembership, Card, ChecklistItem, Column, Comment

# Operation groups from the capability matrix in design.md.
READ_BOARD_CONTENT = "read_board_content"
CARD_WRITE = "card_write"
COMMENT_WRITE = "comment_write"
ACTIVITY_SEARCH_NOTIFICATIONS_ANALYTICS = "activity_search_notifications_analytics"
COLUMN_MANAGE = "column_manage"
BOARD_ADMIN = "board_admin"

GUEST_OPERATIONS = frozenset({READ_BOARD_CONTENT})
MEMBER_OPERATIONS = GUEST_OPERATIONS | {
    CARD_WRITE,
    COMMENT_WRITE,
    ACTIVITY_SEARCH_NOTIFICATIONS_ANALYTICS,
}
ADMIN_OPERATIONS = MEMBER_OPERATIONS | {COLUMN_MANAGE, BOARD_ADMIN}

ROLE_CAPABILITIES: dict[str, frozenset[str]] = {
    "guest": GUEST_OPERATIONS,
    "member": frozenset(MEMBER_OPERATIONS),
    "admin": frozenset(ADMIN_OPERATIONS),
}

RequiredRole = Literal["member", "admin"]

# The decorator argument maps to the weakest operation of that level.
_REQUIRED_ROLE_OPERATION: dict[str, str] = {
    "member": CARD_WRITE,
    "admin": COLUMN_MANAGE,
}


def role_allows(role: str | None, operation: str) -> bool:
    """Pure decision: allow iff the role's capability set includes the operation.

    A missing or unknown role (no membership, no active link) is always denied.
    """
    if role is None:
        return False
    return operation in ROLE_CAPABILITIES.get(role, frozenset())


def _resolve_board_id(route_params: dict[str, object]) -> uuid.UUID:
    """Find the Board a request targets from its route parameters."""
    board_id = route_params.get("board_id")
    if isinstance(board_id, uuid.UUID):
        return board_id

    resolvers: tuple[
        tuple[str, type[Column] | type[Card] | type[Comment] | type[ChecklistItem]], ...
    ] = (
        ("column_id", Column),
        ("card_id", Card),
        ("comment_id", Comment),
        ("item_id", ChecklistItem),
    )
    for param, model in resolvers:
        value = route_params.get(param)
        if not isinstance(value, uuid.UUID):
            continue
        if model is Comment:
            resolved = (
                db.session.query(Card.board_id)
                .join(Comment, Comment.card_id == Card.id)
                .filter(Comment.id == value)
                .scalar()
            )
        elif model is ChecklistItem:
            resolved = (
                db.session.query(Card.board_id)
                .join(ChecklistItem, ChecklistItem.card_id == Card.id)
                .filter(ChecklistItem.id == value)
                .scalar()
            )
        else:
            resolved = db.session.query(model.board_id).filter(model.id == value).scalar()
        if resolved is None:
            raise NotFoundError("Resource not found")
        assert isinstance(resolved, uuid.UUID)
        return resolved

    # No Board can be resolved: deny rather than let the handler run unchecked.
    raise AuthorizationError("Access denied")


def get_board_role(board_id: uuid.UUID, user_id: uuid.UUID) -> str | None:
    """Read the caller's role from stored BoardMembership (never from the token)."""
    role = (
        db.session.query(BoardMembership.role)
        .filter(BoardMembership.board_id == board_id, BoardMembership.user_id == user_id)
        .scalar()
    )
    return role if isinstance(role, str) else None


def require_role[**P, R](minimum: RequiredRole) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Authenticate, resolve the Board from route params, then check the stored role."""
    operation = _REQUIRED_ROLE_OPERATION[minimum]

    def decorator(view: Callable[P, R]) -> Callable[P, R]:
        @wraps(view)
        def authorized(*args: P.args, **kwargs: P.kwargs) -> R:
            board_id = _resolve_board_id(dict(kwargs))
            role = get_board_role(board_id, current_user().id)
            if not role_allows(role, operation):
                raise AuthorizationError("You do not have permission to perform this action")
            return view(*args, **kwargs)

        # Authentication runs first (R12.6); token_required wraps the RBAC check.
        return token_required(authorized)

    return decorator


__all__ = [
    "ADMIN_OPERATIONS",
    "MEMBER_OPERATIONS",
    "GUEST_OPERATIONS",
    "ROLE_CAPABILITIES",
    "current_user",
    "get_board_role",
    "require_role",
    "role_allows",
]
