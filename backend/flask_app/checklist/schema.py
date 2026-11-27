from marshmallow import fields, validate

from flask_app.common.validation import BaseSchema, TrimmedStr

_TEXT = validate.Length(min=1, max=255)


class CreateChecklistItemSchema(BaseSchema):
    text = TrimmedStr(required=True, validate=_TEXT)


class UpdateChecklistItemSchema(BaseSchema):
    text = TrimmedStr(validate=_TEXT)
    # Only JSON true/false: strings such as "yes" or numbers are rejected.
    is_done = fields.Bool(truthy={True}, falsy={False})
