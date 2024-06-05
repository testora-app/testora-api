from typing import Dict

from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes,LoginSchema
from app._shared.api_errors import error_response, unauthorized_request, success_response, not_found, bad_request, unapproved_account
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.test.operations import question_manager, test_manager
from app.test.schemas import TestListSchema, QuestionListSchema, Responses, QuestionSchema, TestSchema


testr = APIBlueprint('testr', __name__)


@testr.get("/questions/")
@testr.output(QuestionListSchema, 200)
def get_questions():
    questions = question_manager.get_questions()
    return success_response(data=[question.to_json() for question in questions])

@testr.post("/questions/")
@testr.input(QuestionSchema)
@testr.output(Responses.QuestionSchema)
def post_questions(json_data):
    sub = json_data.pop('sub_questions')
    new_question = question_manager.create_question(**json_data)
    question_manager.create_subquestion(new_question.id, **sub)
    return success_response(data=new_question.to_json())


@testr.post("/questions-multiple/")
@testr.input(QuestionSchema)
@testr.output(Responses.QuestionSchema)
def post_multiple(json_data):
    questions = question_manager.save_multiple_questions(json_data)
    return success_response(data=[question.to_json() for question in questions])


@testr.get("/questions/<int:question_id>/")
@testr.input(QuestionSchema)
@testr.output(Responses.QuestionSchema)
def edit_questions(question_id, json_data):
    # implement edit
    question = question_manager.get_question_by_id(question_id)

    return success_response(data=question.to_json())

@testr.delete("/questions/<int:question_id>/")
@testr.output(SuccessMessage)
def delete_questions(question_id):
    question = question_manager.get_question_by_id(question_id)
    subquestions = question_manager.get_subquestion_by_parent(question_id)

    if question:
        for sub in subquestions:
            sub.delete()

        question.delete()
    return success_response()


# create test
# the different test modes and how they would work