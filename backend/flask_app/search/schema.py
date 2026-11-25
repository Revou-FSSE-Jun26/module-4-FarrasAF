from marshmallow import validate

from flask_app.common.validation import BaseSchema, TrimmedStr


class SearchQuerySchema(BaseSchema):
    q = TrimmedStr(required=True, validate=validate.Length(min=1, max=100))
