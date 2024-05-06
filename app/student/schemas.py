from apiflask.fields import Integer, String, Boolean, List, Nested
from apiflask.validators import Email, Length
from app._shared.schemas import BaseSchema, ID_FIELD
from app.school.schemas import SchoolSchema


class StudentRegister(BaseSchema):
    email = String(required=True, allow_none=False, validate=[Email()])
    first_name = String(required=True, allow_none=False, validate=[Length(min=1)])
    surname = String(required=True, allow_none=False, validate=[Length(min=1)])
    other_names = String(required=False, allow_none=True, validate=[Length(min=1)])
    password = String(required=True, allow_none=False, validate=[Length(min=8)])
    school_code = String(required=True, allow_none=True)


class StudentSchema(BaseSchema):
    id = ID_FIELD
    email = String(required=True, allow_none=False, validate=[Email()])
    first_name = String(required=True, allow_none=False, validate=[Length(min=3)])
    surname = String(required=True, allow_none=False, validate=[Length(min=3)])
    other_names = String(required=False, allow_none=True, validate=[Length(min=1)])
    password = String(required=True, allow_none=False, validate=[Length(min=8)])
    is_approved = Boolean(required=False, allow_none=False)
    is_archived = Boolean(required=False, allow_none=False)
    school_id = ID_FIELD


class VerifiedStudentSchema(BaseSchema):
    student = Nested(StudentSchema)
    auth_token = String()
    school = Nested(SchoolSchema)