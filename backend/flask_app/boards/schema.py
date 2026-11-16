from typing import Any

from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields, validate

from flask_app.common.validation import BaseSchema, TrimmedStr

_NAME = validate.Length(min=1, max=100)
_DESCRIPTION = validate.Length(max=2000)
_VISIBILITY = validate.OneOf(["private", "team"])


class ArchivedFlag(fields.Field[bool]):
    """`?archived` (bare), `?archived=true` or `?archived=false`."""

    def _deserialize(self, value: Any, attr: str | None, data: Any, **kwargs: Any) -> bool:
        if value in ("", "true"):
            return True
        if value == "false":
            return False
        raise MarshmallowValidationError("Must be true or false.")


class CreateBoardSchema(BaseSchema):
    team_id = fields.UUID(required=True)
    name = TrimmedStr(required=True, validate=_NAME)


class UpdateBoardSchema(BaseSchema):
    name = TrimmedStr(validate=_NAME)
    description = fields.String(validate=_DESCRIPTION)
    visibility = fields.String(validate=_VISIBILITY)


class ListBoardsQuerySchema(BaseSchema):
    archived = ArchivedFlag()
