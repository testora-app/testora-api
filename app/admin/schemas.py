from apiflask.fields import Integer, String, Boolean, List, Nested
from marshmallow.exceptions import ValidationError

from app._shared.schemas import BaseSchema


class AddAdminSchema(BaseSchema):
    email = String(required=True, allow_none=False)
    password = String(required=True, allow_none=False)
    username = String(required=True, allow_none=False)
    is_super_admin = Boolean(required=True, allow_none=False)


class AdminSchema(BaseSchema):
    id = Integer(required=True)
    email = String(required=True, allow_none=False)
    password = String(required=True, allow_none=False)
    username = String(required=True, allow_none=False)
    is_super_admin = Boolean(required=True, allow_none=False)


class AdminListSchema(BaseSchema):
    data = List(Nested(AdminSchema))


class VerifiedAdminSchema(BaseSchema):
    user = Nested(AdminSchema)
    auth_token = String(required=True, allow_none=False)