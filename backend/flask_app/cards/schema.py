from marshmallow import fields, validate

from flask_app.common.validation import BaseSchema, TrimmedStr

_TITLE = validate.Length(min=1, max=255)
_DESCRIPTION = validate.Length(max=5000)


class CreateCardSchema(BaseSchema):
    title = TrimmedStr(required=True, validate=_TITLE)
    description = fields.Str(validate=_DESCRIPTION)
    assignee_id = fields.UUID(allow_none=True)
    due_date = fields.Date(allow_none=True)


class MoveCardSchema(BaseSchema):
    target_column_id = fields.UUID(required=True)
    target_index = fields.Int(required=True, strict=True)


class UpdateCardSchema(BaseSchema):
    title = TrimmedStr(validate=_TITLE)
    description = fields.Str(validate=_DESCRIPTION)
    assignee_id = fields.UUID(allow_none=True)
    due_date = fields.Date(allow_none=True)
    version = fields.Int(strict=True)  # missing -> ConflictError in the service
