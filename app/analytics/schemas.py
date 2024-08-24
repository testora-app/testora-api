from apiflask.fields import Float, String

from app._shared.schemas import BaseSchema, make_response_schema

class WeeklyReportSchema(BaseSchema):
    hours_spent = Float(required=True)
    percentage = Float(required=True)


class Responses:
    WeeklyReportSchema = make_response_schema(WeeklyReportSchema)