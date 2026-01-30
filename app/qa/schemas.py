"""
Schemas for Q&A API requests and responses
"""
from apiflask import Schema
from apiflask.fields import Integer, String, DateTime, Nested, Dict
from apiflask.validators import Length, OneOf


class QuestionSchema(Schema):
    """Schema for asking a question to ChatGPT"""
    student_id = Integer(required=True)
    school_id = Integer(required=True)
    subject = String(required=True, validate=Length(min=1, max=100))
    topic = String(required=True, validate=Length(min=1, max=200))
    question = String(required=True, validate=Length(min=5, max=1000))


class QuestionRequestSchema(Schema):
    """Wrapper schema with data field following API convention"""
    data = Nested(QuestionSchema)


class QuestionResponseData(Schema):
    """Schema for the answer response data"""
    answer = String()
    topic = String()
    timestamp = DateTime()


class QuestionResponseSchema(Schema):
    """Schema for the full answer response"""
    success = String()
    data = Nested(QuestionResponseData)


class QuestionsListSchema(Schema):
    """Schema for listing stored questions"""
    id = Integer()
    student_id = Integer()
    school_id = Integer()
    subject = String()
    topic = String()
    question = String()
    answer = String()
    created_at = DateTime()


class QuestionsListResponseSchema(Schema):
    """Schema for the response when listing questions"""
    success = String()
    data = Nested(QuestionsListSchema(many=True))