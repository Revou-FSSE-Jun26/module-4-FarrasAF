"""Typed domain errors, mapped centrally to the JSON error envelope in app.py."""

VALIDATION_ERROR = "validation_error"
AUTHENTICATION_ERROR = "authentication_error"
AUTHORIZATION_ERROR = "authorization_error"
NOT_FOUND = "not_found"
CONFLICT = "conflict"
INTERNAL_ERROR = "internal_error"


class AppError(Exception):
    """Base class. Never raised directly; raise one of the subclasses."""

    status_code = 500
    code = INTERNAL_ERROR

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class ValidationError(AppError):
    status_code = 400
    code = VALIDATION_ERROR


class AuthenticationError(AppError):
    status_code = 401
    code = AUTHENTICATION_ERROR


class AuthorizationError(AppError):
    status_code = 403
    code = AUTHORIZATION_ERROR


class NotFoundError(AppError):
    status_code = 404
    code = NOT_FOUND


class ConflictError(AppError):
    status_code = 409
    code = CONFLICT
