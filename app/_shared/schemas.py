from typing import Any

from apiflask import Schema
from apiflask.fields import Integer, String, Nested, Dict
from marshmallow.exceptions import ValidationError

from .api_errors import BaseError

ID_FIELD = Integer(allow_none=False, required=True)

class BaseSchema(Schema):
    def handle_error(self, error: ValidationError, data: Any, *, many: bool, **kwargs):
        raise BaseError("Validation Error", error_code=422, payload=error.messages_dict)

class SuccessMessage(Schema):
    message = String(default='success')

class GenericSchema(Schema):
    action = String(allow_none=True, required=False)


class LoginSchema(BaseSchema):
    email = String(allow_none=False, required=True)
    password = String(allow_none=False, required=True)


def make_response_schema(schema: BaseSchema):
    class Response(BaseSchema):
        data = Nested(schema)

    response_data = Response()
    return response_data


class UserTypes:
    admin = 'super_admin'
    school_admin = 'Admin'
    staff = 'Teacher'
    student = 'Student'


class CurriculumTypes:
    bece = 'bece'