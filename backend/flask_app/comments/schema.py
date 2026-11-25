from marshmallow import fields, validate

from flask_app.common.validation import BaseSchema, NonBlankStr

_BODY = validate.Length(min=1, max=5000)


class CreateCommentSchema(BaseSchema):
    body = NonBlankStr(required=True, validate=_BODY)
    parent_comment_id = fields.UUID(allow_none=True)


class UpdateCommentSchema(BaseSchema):
    body = NonBlankStr(required=True, validate=_BODY)
    version = fields.Int(strict=True)  # missing -> ConflictError in the service
