from apiflask.fields import Integer, String, Boolean, List, Nested, Date, Float
from apiflask.validators import Email, Length
from app._shared.schemas import BaseSchema, ID_FIELD, make_response_schema
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
    current_streak = Integer(required=False)
    highest_streak = Integer(required=False)
    last_login = DateTime(required=False)
    is_approved = Boolean(required=False, allow_none=False)
    is_archived = Boolean(required=False, allow_none=False)
    school_id = ID_FIELD


class VerifiedStudentSchema(BaseSchema):
    user = Nested(StudentSchema)
    auth_token = String()
    school = Nested(SchoolSchema)
    user_type = String(required=True)


class BatchSchema(BaseSchema):
    id = Integer(required=True, allow_none=False, dump_only=True)
    batch_name = String(required=True, allow_none=False)
    curriculum = String(required=True, allow_none=False)
    students = List(Integer(), allow_none=True, required=False)


class BatchListSchema(BaseSchema):
    data = List(Nested(BatchSchema))


class ApproveStudentSchema(BaseSchema):
    student_ids = List(ID_FIELD)


class GetStudentListSchema(BaseSchema):
    data = List(Nested(StudentSchema))


class EndSessionSchema(BaseSchema):
    student_id = Integer(required=True, allow_none=False)
    date = Date(required=True, allow_none=False)
    duration = Float(required=True, allow_none=False)



class Requests:
    CreateBatchSchema = make_response_schema(BatchSchema)
    EndSessionSchema = make_response_schema(EndSessionSchema, is_list=True)


class Responses:
    VerifiedStudentSchema = make_response_schema(VerifiedStudentSchema)
    StudentSchema = make_response_schema(StudentSchema)
    BatchSchema = make_response_schema(BatchSchema)