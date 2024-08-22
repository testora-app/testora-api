from typing import Any
import bisect

from apiflask import Schema
from apiflask.fields import Integer, String, Nested, Dict, List
from apiflask.validators import Range
from marshmallow.exceptions import ValidationError

from .api_errors import BaseError

ID_FIELD = Integer(allow_none=False, required=True)

class BaseSchema(Schema):
    def handle_error(self, error: ValidationError, data: Any, *, many: bool, **kwargs):
        raise BaseError("Validation Error", error_code=422, payload=error.messages_dict)


def make_response_schema(schema: BaseSchema, is_list=False):
    if is_list:
        class ListResponseSchema(Schema):
            data = List(Nested(schema))
        return ListResponseSchema()
    
    class Response(BaseSchema):
        data = Nested(schema)
    return Response()
    

class PaginationQuery(Schema):
    page = Integer(load_default=1)  # set default page to 1
    per_page = Integer(load_default=20, validate=Range(max=5000))

class SuccessMessage(Schema):
    message = String(default='success')

class GenericSchema(Schema):
    action = String(allow_none=True, required=False)


class LoginSchema(BaseSchema):
    email = String(allow_none=False, required=True)
    password = String(allow_none=False, required=True)

class ResetPassword(BaseSchema):
    email = String(allow_none=False, required=True)


class ChangePassword(BaseSchema):
    new_password = String(allow_none=False, required=True)
    confirmation_code = String(allow_none=False, required=True)


ResetPasswordSchema = make_response_schema(ResetPassword)
ChangePasswordSchema = make_response_schema(ChangePassword)





class UserTypes:
    admin = 'super_admin'
    school_admin = 'Admin'
    staff = 'Teacher'
    student = 'Student'


class CurriculumTypes:
    bece = 'bece'

    @classmethod
    def get_curriculum_types(cls):
        return [cls.bece]
    

class ExamModes:
    exam = 'exam'
    level = 'level'

    @classmethod
    def get_valid_exam_modes(cls):
        return [cls.exam, cls.level]
    

class QuestionsNumberLimiter:
    questions_per_level = {
        '1': 10,
        '2': 12,
        '3': 15,
        '4': 18,
        '5': 20,
        '6': 25,
        '7': 30,
        '8': 35,
        '9': 40
    }

    @classmethod
    def get_question_limit_for_level(cls, student_subject_level) -> int:
        return cls.questions_per_level[str(student_subject_level)]
    

class QuestionPoints:
    question_level_points = {
            1: 1.2,
            2: 1.5,
            3: 1.7,
            4: 2,
            5: 2.2,
            6: 2.5,
            7: 2.65,
            8: 2.8,
            9: 3
        }
    
    @classmethod
    def get_question_level_points(cls):
        return cls.question_level_points
    

class LevelLimitPoints:
    points_to_levels = {
        1000: 1,
        2100: 2,
        3200: 3,
        4300: 4,
        5400: 5,
        6500: 6,
        8000: 7,
        10000: 8,
        15000: 9,
        25000: 10
    }

    @classmethod
    def get_points_level(cls, points):
        sorted_points = sorted(cls.points_to_levels.keys())
        index = bisect.bisect_right(sorted_points, points)
        
        if index == 0:
            return 1 # Points less than the smallest threshold
        else:
            return cls.points_to_levels[sorted_points[index - 1]]

