from apiflask import Schema
from apiflask.fields import Float, String, Integer, Nested, List

from app._shared.schemas import BaseSchema, make_response_schema


class WeeklyReportSchema(BaseSchema):
    hours_spent = Float(required=True)
    percentage = Float(required=True)


class TopicPerformanceSchema(BaseSchema):
    topic_name = String(required=True)
    subject_name = String(required=True)
    severity = String(required=False)


class TopicPerformanceQuerySchema(Schema):
    student_id = Integer(required=False, allow_none=False)
    subject_id = Integer(required=False, allow_none=False)
    batch_id = Integer(required=False, allow_none=False)

class PerformanceCategorySchema(BaseSchema):
    student_number = Integer(required=True)
    percent_number = Float(required=True)


class StudentPerformanceSchema(BaseSchema):
    passing = Nested(PerformanceCategorySchema, required=True)
    credit = Nested(PerformanceCategorySchema, required=True)
    failing = Nested(PerformanceCategorySchema, required=True)


class PerformanceSummarySchema(BaseSchema):
    batch_average = Float(required=True)
    test_completion = Float(required=True)
    failing_student_ids = List(Integer(), required=True)


class TopicMasteryItemSchema(BaseSchema):
    topic_name = String(required=True)
    average = Float(required=True)


class TopicMasteryDataSchema(BaseSchema):
    strong_topics = List(Nested(TopicMasteryItemSchema), required=True)
    weak_topics = List(Nested(TopicMasteryItemSchema), required=True)



class Responses:
    WeeklyReportSchema = make_response_schema(WeeklyReportSchema)
    TopicPerformanceSchema = make_response_schema(TopicPerformanceSchema, is_list=True)
    StudentPerformanceSchema = make_response_schema(StudentPerformanceSchema)
    PerformanceSummarySchema = make_response_schema(PerformanceSummarySchema)
    TopicMasteryDataSchema = make_response_schema(TopicMasteryDataSchema)


class Requests:
    TopicPerformanceQuerySchema = TopicPerformanceQuerySchema
