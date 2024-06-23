from typing import Any

from apiflask import Schema
from apiflask.fields import Integer, String, Nested, Dict
from marshmallow.exceptions import ValidationError

from .api_errors import BaseError

ID_FIELD = Integer(allow_none=False, required=True)

class BaseSchema(Schema):
    def handle_error(self, error: ValidationError, data: Any, *, many: bool, **kwargs):
        raise BaseError("Validation Error", error_code=422, payload=error.messages_dict)

class SuccessMessage(Schema):
    message = String(default='success')

class GenericSchema(Schema):
    action = String(allow_none=True, required=False)


class LoginSchema(BaseSchema):
    email = String(allow_none=False, required=True)
    password = String(allow_none=False, required=True)


#TODO: improve this to also create lists
def make_response_schema(schema: BaseSchema):
    class Response(BaseSchema):
        data = Nested(schema)

    response_data = Response()
    return response_data


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