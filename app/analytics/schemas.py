from apiflask import Schema
from apiflask.fields import Float, String, Integer

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


class Responses:
    WeeklyReportSchema = make_response_schema(WeeklyReportSchema)
    TopicPerformanceSchema = make_response_schema(TopicPerformanceSchema, is_list=True)


class Requests:
    TopicPerformanceQuerySchema = TopicPerformanceQuerySchema
