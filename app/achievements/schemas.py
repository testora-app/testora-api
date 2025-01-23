from apiflask import Schema
from apiflask.fields import Float, String, Integer, Nested

from app._shared.schemas import BaseSchema, make_response_schema


class AchievementReport(BaseSchema):
    student_id = Integer(required=True)

class AchievementSchema(BaseSchema):
    name = String(required=True)
    description = String(required=True)
    image_url = String(required=True)


class AchievementResponseSchema(BaseSchema):
    achievement = Nested(AchievementSchema)
    student_id = Integer(required=True)
    number_of_times = Integer(required=True)


class Responses:
    AchievementSchema = make_response_schema(AchievementSchema, is_list=True)
    AchievementResponseSchema = make_response_schema(AchievementResponseSchema, is_list=True)


class Requests:
    AchievementReport = AchievementReport
