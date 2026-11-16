from marshmallow import validate

from flask_app.common.validation import BaseSchema, TrimmedStr


class CreateTeamSchema(BaseSchema):
    name = TrimmedStr(required=True, validate=validate.Length(min=1, max=100))
