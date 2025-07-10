from apiflask.fields import Integer, String, Boolean, List, Nested
from apiflask.validators import OneOf
from apiflask import PaginationSchema

from app._shared.schemas import BaseSchema, CurriculumTypes, make_response_schema


# region Admin Schema
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


# endregion Admin Schema


# region Subject/Topic Schema



class TopicSchema(BaseSchema):
    id = Integer(required=True)
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    subject_id = Integer(required=True, allow_none=False)
    theme_id = Integer(required=True, allow_none=False)
    level = Integer(required=True, allow_none=False)


class AddTopicSchema(BaseSchema):
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    subject_id = Integer(required=True, allow_none=False)
    level = Integer(required=True, allow_none=False)
    theme_id = Integer(required=True, allow_none=False)


class AddTopicSchemaPost(BaseSchema):
    data = List(Nested(AddTopicSchema), min=1)


class TopicSchemaList(BaseSchema):
    data = List(Nested(TopicSchema))


class ThemeSchema(BaseSchema):
    id = Integer(required=True)
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    subject_id = Integer(required=True, allow_none=False)
    topics = List(Nested(TopicSchema), required=False, allow_none=True)


class AddThemeSchema(BaseSchema):
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    subject_id = Integer(required=True, allow_none=False)


class AddThemeSchemaPost(BaseSchema):
    data = List(Nested(AddThemeSchema), min=1)


class ThemeSchemaList(BaseSchema):
    data = List(Nested(ThemeSchema))


class SubjectSchema(BaseSchema):
    id = Integer(required=True)
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    curriculum = String(
        required=True, allow_none=False, validate=[OneOf(CurriculumTypes.bece)]
    )
    themes = List(Nested(ThemeSchema), required=False, allow_none=True)


class AddSubjectSchema(BaseSchema):
    name = String(required=True, allow_none=False)
    short_name = String(required=False, allow_none=True)
    curriculum = String(
        required=True, allow_none=False, validate=[OneOf(CurriculumTypes.bece)]
    )


class AddSubjectSchemaPost(BaseSchema):
    data = List(Nested(AddSubjectSchema), min=1)


class SubjectSchemaList(BaseSchema):
    data = List(Nested(SubjectSchema))
    pagination = Nested(PaginationSchema)

# endregion Subject/Topic Schema

class CurriculumSchema(BaseSchema):
    name = String(required=True, allow_none=False)
    display_name = String(required=True, allow_none=False)


# region Nested Responses
class Responses:
    AdminResponseSchema = make_response_schema(AddAdminSchema)
    VerifiedAdminResponse = make_response_schema(VerifiedAdminSchema)
    SubjectSchema = make_response_schema(SubjectSchema)
    TopicSchema = make_response_schema(TopicSchema)
    ThemeSchema = make_response_schema(ThemeSchema)
    CurriculumSchema = make_response_schema(CurriculumSchema, is_list=True)

class Requests:
    EditSubjectSchema = make_response_schema(SubjectSchema)
    EditTopicSchema = make_response_schema(TopicSchema)
    EditThemeSchema = make_response_schema(ThemeSchema)
    AddAdminSchema = make_response_schema(AddAdminSchema)


# endregion
