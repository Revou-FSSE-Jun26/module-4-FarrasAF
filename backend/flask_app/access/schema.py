from marshmallow import fields, validate

from flask_app.common.validation import BaseSchema

BOARD_ROLES = ("member", "admin")


class AddMemberSchema(BaseSchema):
    user_id = fields.UUID(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(BOARD_ROLES))


class ChangeMemberRoleSchema(BaseSchema):
    role = fields.Str(required=True, validate=validate.OneOf(BOARD_ROLES))
