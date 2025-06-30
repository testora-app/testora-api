from apiflask.schemas import Schema
from apiflask.fields import (
    Integer,
    String,
    Boolean,
    List,
    Nested,
    DateTime,
    Dict,
    Decimal,
)
from app._shared.schemas import BaseSchema, ID_FIELD, make_response_schema


class SubQuestionSchema(BaseSchema):
    id = Integer(dump_only=True)
    parent_question_id = Integer(dump_only=True)
    text = String(required=True)
    correct_answer = String(required=True)
    possible_answers = List(String(), required=True)
    points = Integer(required=True)
    flag_reason = String(allow_none=True, required=False)
    is_flagged = Boolean(allow_none=True, required=False)
    year = Integer(allow_none=True, required=False)


class QuestionImageSchema(Schema):
    image_url = String(required=True)
    label = String(allow_none=True, required=False)
    is_for_answer = Boolean(allow_none=True, required=False)

class QuestionSchema(BaseSchema):
    id = Integer(dump_only=True)
    text = String(required=True)
    correct_answer = String(required=True, allow_none=True)
    possible_answers = List(String(), required=True, allow_none=True)
    topic_id = Integer(required=True)
    points = Integer(required=True, allow_none=True)
    school_id = Integer(allow_none=True)
    flag_reason = String(allow_none=True, required=False)
    is_flagged = Boolean(allow_none=True, required=False)
    sub_questions = List(Nested(SubQuestionSchema), required=False, allow_none=True)
    year = Integer(allow_none=True, required=False)
    is_instructional = Boolean(allow_none=True, required=False, missing=False)
    images = List(Nested(QuestionImageSchema), required=False, allow_none=True)

class QuestionListSchema(BaseSchema):
    data = List(Nested(QuestionSchema))


class CreateTestSchema(BaseSchema):
    mode = String(required=True, allow_none=False)
    subject_id = Integer(required=True, allow_none=False)


class TestQuestionsSchema(BaseSchema):
    id = Integer(dump_only=True)
    text = String(required=True)
    possible_answers = List(String(), required=True)
    topic_id = Integer(required=True)
    school_id = Integer(allow_none=True)
    flag_reason = String(allow_none=True, required=False)
    is_flagged = Boolean(allow_none=True, required=False)
    sub_questions = List(Nested(SubQuestionSchema), required=False, allow_none=True)
    answer_images = Dict(allow_none=True, required=False)
    question_images = Dict(allow_none=True, required=False)


class TestQuestionsListSchema(BaseSchema):
    data = List(Nested(TestQuestionsSchema))


class SubmittedSubQuestionSchema(BaseSchema):
    id = Integer()
    text = String(required=True)
    student_answer = String(required=True)
    possible_answers = List(String(), required=True)
    parent_question_id = Integer(required=False, allow_none=True)
    points = Integer(required=False, allow_none=True)
    year = Integer(allow_none=True, required=False)
    flag_reason = String(allow_none=True, required=False)
    is_flagged = Boolean(allow_none=True, required=False)


class SubmittedQuestionsSchema(BaseSchema):
    id = Integer()
    index = Integer(required=False)
    level = Integer(required=False, allow_none=True)
    points = Integer(required=False, allow_none=True)
    text = String(required=True)
    possible_answers = List(String(), required=True)
    student_answer = String(required=True)
    topic_id = Integer(required=True)
    school_id = Integer(allow_none=True)
    meta = Dict(allow_none=True, required=False)
    opened = Boolean(allow_none=True, required=False)
    options = Dict(allow_none=True, required=False)
    flag_reason = String(allow_none=True, required=False)
    is_flagged = Boolean(allow_none=True, required=False)
    year = Integer(allow_none=True, required=False)
    sub_questions = List(
        Nested(SubmittedSubQuestionSchema), required=False, allow_none=True
    )

    # TODO: REMOVETHIS
    correct_answer = String(allow_none=True, required=False)


class FlagQuestionSchema(Schema):
    question_id = Integer(required=True)
    flag_reason = List(String(), required=True)


class TestSchema(BaseSchema):
    id = Integer(dump_only=True)
    student_id = Integer(required=True)
    subject_name = String(required=False, allow_none=False)
    questions = List(Nested(TestQuestionsSchema))
    total_points = Integer(required=True)
    points_acquired = Integer(required=True)
    total_score = Decimal(required=True)
    score_acquired = Decimal(required=True)
    started_on = DateTime(required=True)
    finished_on = DateTime(allow_none=True)
    question_number = Integer(allow_none=True)
    questions_correct = Integer(allow_none=True)
    meta = Dict(allow_none=True)
    is_completed = Boolean(required=True)
    school_id = Integer(allow_none=True)
    created_at = DateTime(required=True)
    duration = Integer(required=True, allow_none=False)


class TestListSchema(BaseSchema):
    data = List(Nested(TestSchema))


class MarkTestSchema(BaseSchema):
    questions = List(Nested(SubmittedQuestionsSchema))
    meta = Dict(allow_none=True, required=False)


class TestQuerySchema(Schema):
    student_id = Integer(allow_none=True, required=False)


class SubjectPerformance(Schema):
    subject_id = Integer(allow_none=True, required=False)
    subject_name = String(allow_none=True, required=False)
    average_score = Decimal(allow_none=True, required=False)


class SubjectPerformances(Schema):
    best_performing_subjects = List(Nested(SubjectPerformance))
    worst_performing_subjects = List(Nested(SubjectPerformance))


class Responses:
    QuestionSchema = make_response_schema(QuestionSchema)
    TestSchema = make_response_schema(TestSchema)
    SubjectPerformances = make_response_schema(SubjectPerformances)


class Requests:
    AddQuestionSchema = make_response_schema(QuestionSchema)
    EditQuestionSchema = make_response_schema(QuestionSchema)
    CreateTestSchema = make_response_schema(CreateTestSchema)
    MarkTestSchema = make_response_schema(MarkTestSchema)
    FlagQuestionSchema = make_response_schema(FlagQuestionSchema, is_list=True)
