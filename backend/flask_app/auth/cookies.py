"""The only place auth cookies are set or cleared."""

from flask import Response, current_app

REFRESH_COOKIE_PATH = "/api/auth/refresh"
LOGOUT_COOKIE_PATH = "/api/auth/logout"


def _set_cookie(response: Response, name: str, value: str, max_age: int, path: str) -> None:
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        path=path,
        secure=bool(current_app.config["COOKIE_SECURE"]),
        httponly=True,
        samesite="Lax",
    )


def set_access_cookie(response: Response, access_token: str) -> None:
    config = current_app.config
    _set_cookie(
        response,
        config["ACCESS_COOKIE_NAME"],
        access_token,
        config["ACCESS_TOKEN_MINUTES"] * 60,
        "/",
    )


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    config = current_app.config
    set_access_cookie(response, access_token)
    max_age = config["REFRESH_TOKEN_DAYS"] * 86400
    # The cookie path is a prefix match, so two cookies cover both endpoints.
    for path in (REFRESH_COOKIE_PATH, LOGOUT_COOKIE_PATH):
        _set_cookie(response, config["REFRESH_COOKIE_NAME"], refresh_token, max_age, path)


def clear_auth_cookies(response: Response) -> None:
    config = current_app.config
    secure = bool(config["COOKIE_SECURE"])
    response.delete_cookie(
        config["ACCESS_COOKIE_NAME"], path="/", secure=secure, httponly=True, samesite="Lax"
    )
    for path in (REFRESH_COOKIE_PATH, LOGOUT_COOKIE_PATH):
        response.delete_cookie(
            config["REFRESH_COOKIE_NAME"],
            path=path,
            secure=secure,
            httponly=True,
            samesite="Lax",
        )
