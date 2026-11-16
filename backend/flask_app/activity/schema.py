import re
from typing import Any

from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields

from flask_app.common.validation import BaseSchema

_INTEGER = re.compile(r"-?[0-9]+")


class StrictInt(fields.Field[int]):
    """Integer from a query string: only plain digits (optional minus), no floats or spaces."""

    def _deserialize(self, value: Any, attr: str | None, data: Any, **kwargs: Any) -> int:
        if isinstance(value, bool) or not (
            isinstance(value, int) or (isinstance(value, str) and _INTEGER.fullmatch(value))
        ):
            raise MarshmallowValidationError("Not a valid integer.")
        return int(value)


class ActivityQuerySchema(BaseSchema):
    page = StrictInt()
