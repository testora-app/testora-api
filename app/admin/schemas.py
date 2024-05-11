from apiflask.fields import Integer, String, Boolean, List, Nested
from apiflask.validators import OneOf

from app._shared.schemas import BaseSchema, CurriculumTypes, make_response_schema

#region Admin Schema
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

#endregion Admin Schema


#region Subject/Topic Schema
class SubjectSchema(BaseSchema):
    id = Integer(required=True)
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    curriculum = String(required=True, allow_none=False, validate=[OneOf(CurriculumTypes.bece)])


class AddSubjectSchema(BaseSchema):
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    curriculum = String(required=True, allow_none=False, validate=[OneOf(CurriculumTypes.bece)])


class AddSubjectSchemaPost(BaseSchema):
    data = List(Nested(AddSubjectSchema), min=1)

class SubjectSchemaList(BaseSchema):
    data = List(Nested(SubjectSchema))


class TopicSchema(BaseSchema):
    id = Integer(required=True)
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    subject_id = Integer(required=True, allow_none=False)
    level = Integer(required=True, allow_none=False)


class AddTopicSchema(BaseSchema):
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    subject_id = Integer(required=True, allow_none=False)
    level = Integer(required=True, allow_none=False)


class AddTopicSchemaPost(BaseSchema):
    data = List(Nested(AddTopicSchema), min=1)

class TopicSchemaList(BaseSchema):
    data = List(Nested(TopicSchema))

#endregion Subject/Topic Schema

#region Nested Responses
class Responses:
    AdminResponseSchema = make_response_schema(AddAdminSchema)
    VerifiedAdminResponse = make_response_schema(VerifiedAdminSchema)
    SubjectSchema = make_response_schema(SubjectSchema)
    TopicSchema = make_response_schema(TopicSchema)

#endregion 
