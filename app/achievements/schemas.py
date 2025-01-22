from apiflask import Schema
from apiflask.fields import Float, String, Integer

from app._shared.schemas import BaseSchema, make_response_schema


class AchievementReport(BaseSchema):
    student_id = Integer(required=True)

class AchievementSchema(BaseSchema):
    name = String(required=True)
    description = String(required=True)
    image_url = String(required=True)


class Responses:
    AchievementSchema = make_response_schema(AchievementSchema, is_list=True)


class Requests:
    AchievementReport = AchievementReport
