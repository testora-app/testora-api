from apiflask.fields import String, List, Nested, Date
from app._shared.schemas import BaseSchema, ID_FIELD, make_response_schema


class SchoolSchema(BaseSchema):
    id = ID_FIELD
    name = String(required=True, allow_none=False)
    location = String(required=True, allow_none=True)
    logo = String(required=False, allow_none=False)
    short_name = String(required=False, allow_none=False)
    phone_number = String(required=False, allow_none=False)
    email = String(required=False, allow_none=False)
    code = String(required=False, allow_none=True)
    subscription_package = String(required=False, allow_none=False)
    subscription_expiry_date = Date(required=False, allow_none=True)
    subscription_package_description = String(required=False, allow_none=True)


class AddSchoolSchema(BaseSchema):
    data = Nested(SchoolSchema, exclude=("id", "code"))


class GetSchoolSchema(BaseSchema):
    data = Nested(SchoolSchema)


class GetSchoolListSchema(BaseSchema):
    data = List(Nested(SchoolSchema))


class Responses:
    GetSchoolSchema = make_response_schema(GetSchoolSchema)
