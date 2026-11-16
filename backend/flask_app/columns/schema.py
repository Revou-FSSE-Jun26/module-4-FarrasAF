from marshmallow import fields, validate

from flask_app.common.validation import BaseSchema, TrimmedStr

_NAME = validate.Length(min=1, max=100)


class CreateColumnSchema(BaseSchema):
    name = TrimmedStr(required=True, validate=_NAME)


class RenameColumnSchema(BaseSchema):
    name = TrimmedStr(required=True, validate=_NAME)


class ReorderColumnSchema(BaseSchema):
    target_index = fields.Int(required=True, strict=True)
