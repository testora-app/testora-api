from apiflask.fields import Integer, String, Boolean, List, Nested, DateTime, Dict, Decimal
from app._shared.schemas import BaseSchema, ID_FIELD, make_response_schema


class SubQuestionSchema(BaseSchema):
    id = Integer(dump_only=True)
    parent_question_id = Integer(required=True)
    text = String(required=True)
    correct_answer = String(required=True)
    possible_answers = List(String(), required=True)
    points = Integer(required=True)


class QuestionSchema(BaseSchema):
    id = Integer(dump_only=True)
    text = String(required=True)
    correct_answer = String(required=True)
    possible_answers = List(String(), required=True)
    sub_topic_id = Integer(allow_none=True)
    topic_id = Integer(required=True)
    points = Integer(required=True)
    school_id = Integer(allow_none=True)
    sub_questions = List(Nested(SubQuestionSchema), required=False, allow_none=True)


class TestSchema(BaseSchema):
    id = Integer(dump_only=True)
    student_id = Integer(required=True)
    questions = Dict(required=True)
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


class TestListSchema(BaseSchema):
    data = List(Nested(TestSchema))

class QuestionListSchema(BaseSchema):
    data = List(Nested(QuestionSchema))

class CreateTestSchema(BaseSchema):
    mode = String(required=True, allow_none=False)
    subject_id = Integer(required=True, allow_none=False)


class TestQuestionsSchema(BaseSchema):
    id = Integer(dump_only=True)
    text = String(required=True)
    possible_answers = List(String(), required=True)
    sub_topic_id = Integer(allow_none=True)
    topic_id = Integer(required=True)
    school_id = Integer(allow_none=True)
    sub_questions = List(Nested(SubQuestionSchema), required=False, allow_none=True)


class TestQuestionsListSchema(BaseSchema):
    data = List(Nested(TestQuestionsSchema))


class SubmittedSubQuestionSchema(BaseSchema):
    id = Integer()
    text = String(required=True)
    student_answer = String(required=True)
    possible_answers = List(String(), required=True)


class SubmittedQuestionsSchema(BaseSchema):
    id = Integer()
    level = Integer(required=False, allow_none=True)
    points = Integer(required=False)
    text = String(required=True)
    possible_answers = List(String(), required=True)
    student_answer = String(required=True)
    sub_topic_id = Integer(allow_none=True)
    topic_id = Integer(required=True)
    school_id = Integer(allow_none=True)
    meta = Dict(allow_none=True, required=False)
    opened = Boolean(allow_none=True, required=False)
    options = Dict(allow_none=True, required=False)
    sub_questions = List(Nested(SubmittedSubQuestionSchema), required=False, allow_none=True)

    #TODO: REMOVETHIS
    correct_answer = String(allow_none=True, required=False)


class MarkTestSchema(BaseSchema):
    questions = List(Nested(SubmittedQuestionsSchema))
    meta = Dict(allow_none=True, required=False)


class Responses:
    QuestionSchema = make_response_schema(QuestionSchema)
    TestSchema = make_response_schema(TestSchema)


class Requests:
    AddQuestionSchema = make_response_schema(QuestionSchema)
    EditQuestionSchema = make_response_schema(QuestionSchema)
    CreateTestSchema = make_response_schema(CreateTestSchema)
    MarkTestSchema = make_response_schema(MarkTestSchema)