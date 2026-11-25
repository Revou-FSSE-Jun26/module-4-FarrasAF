from marshmallow import fields

from flask_app.common.validation import BaseSchema


class NotificationsQuerySchema(BaseSchema):
    cursor = fields.String()
    unread_only = fields.Boolean()
