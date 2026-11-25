from marshmallow import fields, validate

from flask_app.common.validation import BaseSchema, TrimmedStr


class RegisterSchema(BaseSchema):
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.String(required=True, validate=validate.Length(min=8))
    display_name = TrimmedStr(required=True, validate=validate.Length(min=1, max=50))


class UpdateProfileSchema(BaseSchema):
    display_name = TrimmedStr(required=True, validate=validate.Length(min=1, max=50))


class ChangePasswordSchema(BaseSchema):
    new_password = fields.String(required=True, validate=validate.Length(min=8))
    current_password = fields.String(required=True)


class LoginSchema(BaseSchema):
    email = fields.String(required=True)
    password = fields.String(required=True)
