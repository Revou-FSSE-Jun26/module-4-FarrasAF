from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import current_app, g, request

from flask_app.auth.service import decode_access_token, get_user_by_id
from flask_app.common.exceptions import AuthenticationError
from flask_app.models import User


def token_required[**P, R](view: Callable[P, R]) -> Callable[P, R]:
    """Authenticate from the access cookie and load the User before the handler runs."""

    @wraps(view)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        token = request.cookies.get(current_app.config["ACCESS_COOKIE_NAME"])
        if not token:
            raise AuthenticationError("Authentication required")
        g.current_user = get_user_by_id(decode_access_token(token))
        return view(*args, **kwargs)

    return wrapper


def current_user() -> User:
    user: Any = g.get("current_user")
    if user is None:
        raise AuthenticationError("Authentication required")
    return user  # type: ignore[no-any-return]
