from apiflask.fields import Integer, String, Boolean, List, Nested, Dict
from apiflask.validators import Email, Length
from app._shared.schemas import BaseSchema, ID_FIELD, make_response_schema
from app.school.schemas import SchoolSchema


class StaffRegister(BaseSchema):
    email = String(required=True, allow_none=False, validate=[Email()])
    first_name = String(required=True, allow_none=False, validate=[Length(min=1)])
    surname = String(required=True, allow_none=False, validate=[Length(min=1)])
    other_names = String(required=False, allow_none=True, validate=[Length(min=1)])
    password = String(required=True, allow_none=False, validate=[Length(min=8)])
    school_code = String(required=False, allow_none=True)


class SchoolRegister(BaseSchema):
    name = String(required=True, allow_none=False, validate=[Length(min=3)])
    location = String(required=False, allow_none=True, validate=[Length(min=3)])
    short_name = String(required=True, allow_none=False, validate=[Length(max=11)])

class SchoolAdminRegister(BaseSchema):
    school_admin = Nested(StaffRegister)
    school = Nested(SchoolRegister)


class SchoolAdminRegisterSchema(BaseSchema):
    data = Nested(SchoolAdminRegister)

class StaffRegisterSchema(BaseSchema):
    data = Nested(StaffRegister)


class StaffSchema(BaseSchema):
    id = ID_FIELD
    email = String(required=True, allow_none=False, validate=[Email()])
    first_name = String(required=True, allow_none=False, validate=[Length(min=3)])
    surname = String(required=True, allow_none=False, validate=[Length(min=3)])
    other_names = String(required=False, allow_none=True, validate=[Length(min=1)])
    password = String(required=True, allow_none=False, validate=[Length(min=8)])
    is_approved = Boolean(required=False, allow_none=False)
    batches = List(ID_FIELD, required=False, allow_none=True, validate=[Length(min=0)], dump_only=True)
    subjects = List(ID_FIELD, required=False, allow_none=True, validate=[Length(min=0)])
    school_id = ID_FIELD


class GetStaffSchema(BaseSchema):
    data = Nested(StaffSchema)

class GetStaffListSchema(BaseSchema):
    data = List(Nested(StaffSchema))

class VerifiedStaffSchema(BaseSchema):
    user = Nested(StaffSchema)
    auth_token = String()
    school = Nested(SchoolSchema)
    user_type = String(required=True)


class ApproveStaffSchema(BaseSchema):
    staff_ids = List(ID_FIELD)



class Responses:
    VerifiedStaffSchema = make_response_schema(VerifiedStaffSchema)
    StaffSchema = make_response_schema(StaffSchema)
    
