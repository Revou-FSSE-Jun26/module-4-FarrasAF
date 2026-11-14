from typing import Any

from marshmallow import RAISE, Schema, fields
from marshmallow import ValidationError as MarshmallowValidationError

from flask_app.common.exceptions import ValidationError


class BaseSchema(Schema):
    class Meta:
        unknown = RAISE


class TrimmedStr(fields.String):
    """String trimmed before validators run, so lengths count after trimming."""

    def _deserialize(self, value: Any, attr: str | None, data: Any, **kwargs: Any) -> str:
        return super()._deserialize(value, attr, data, **kwargs).strip()


class NonBlankStr(fields.String):
    """String that must contain a non-whitespace character; stored unchanged."""

    def _deserialize(self, value: Any, attr: str | None, data: Any, **kwargs: Any) -> str:
        result = super()._deserialize(value, attr, data, **kwargs)
        if not result.strip():
            raise MarshmallowValidationError("Must not be blank.")
        return result


def _first_message(messages: Any) -> str:
    if isinstance(messages, list) and messages:
        return _first_message(messages[0])
    if isinstance(messages, dict) and messages:
        return _first_message(next(iter(messages.values())))
    return str(messages)


def load_schema(schema: Schema, data: Any) -> dict[str, Any]:
    """Validate `data`; raise ValidationError for the first failing field."""
    try:
        result: dict[str, Any] = schema.load(data)
    except MarshmallowValidationError as exc:
        messages = exc.messages
        if isinstance(messages, dict) and messages:
            field, detail = next(iter(messages.items()))
            message = _first_message(detail)
            if field == "_schema":
                raise ValidationError(message) from exc
            raise ValidationError(f"{field}: {message}", field=str(field)) from exc
        raise ValidationError(_first_message(messages)) from exc
    return result
