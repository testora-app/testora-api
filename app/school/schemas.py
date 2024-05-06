from apiflask.fields import Integer, String, Boolean, List, Nested
from app._shared.schemas import BaseSchema, ID_FIELD


class SchoolSchema(BaseSchema):
    id = ID_FIELD
    name = String(required=True, allow_none=False)
    location = String(required=True, allow_none=True)
    logo = String(required=False, allow_none=False)
    short_name = String(required=False, allow_none=False)
    phone_number = String(required=False, allow_none=False)
    email = String(required=False, allow_none=False)
    code = String(required=False, allow_none=True)


class AddSchool(BaseSchema):
    name = String(required=True, allow_none=False)
    location = String(required=True, allow_none=True)
    logo = String(required=False, allow_none=False)
    short_name = String(required=False, allow_none=False)
    phone_number = String(required=False, allow_none=False)
    email = String(required=False, allow_none=False)


class AddSchoolSchema(BaseSchema):
    data = Nested(AddSchool)

class GetSchoolSchema(BaseSchema):
    data = Nested(SchoolSchema)

class GetSchoolListSchema(BaseSchema):
    data = List(Nested(SchoolSchema))