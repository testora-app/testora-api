from app.tests.models import Question, Test
from app._shared.operations import BaseManager

from typing import List


class QuestionManager(object):

    def get_questions():
        return Question.query.all()
    


class TestManager(object):
    
    def get_tests():
        return Test.query.all()



question_manager = QuestionManager()
test_manager = TestManager()