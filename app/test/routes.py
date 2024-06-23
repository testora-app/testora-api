from typing import Dict

from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes, ExamModes
from app._shared.api_errors import error_response, unauthorized_request, success_response, not_found, bad_request, unapproved_account
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.test.operations import question_manager, test_manager
from app.test.schemas import TestListSchema, QuestionListSchema, Responses, QuestionSchema, TestSchema, Requests
from app.test.services import TestService

from app.student.operations import student_manager, stusublvl_manager


testr = APIBlueprint('testr', __name__)


@testr.get("/questions/")
@testr.output(QuestionListSchema, 200)
def get_questions():
    questions = question_manager.get_questions()
    return success_response(data=[question.to_json() for question in questions])

@testr.post("/questions/")
@testr.input(Requests.AddQuestionSchema)
@testr.output(Responses.QuestionSchema)
def post_questions(json_data):
    json_data = json_data["data"]
    sub = json_data.pop('sub_questions')
    new_question = question_manager.create_question(**json_data)
    question_manager.create_subquestion(new_question.id, **sub)
    return success_response(data=new_question.to_json())


@testr.post("/questions-multiple/")
@testr.input(QuestionListSchema)
@testr.output(Responses.QuestionSchema)
def post_multiple(json_data):
    questions = question_manager.save_multiple_questions(json_data["data"])
    return success_response(data=[question.to_json() for question in questions])


@testr.put("/questions/<int:question_id>/")
@testr.input(Requests.EditQuestionSchema)
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
@testr.post("/tests/")
@testr.input(Requests.CreateTestSchema)
@testr.output(Responses.TestSchema, 201)
@token_auth([UserTypes.student])
def create_test(json_data):
    data = json_data["data"]
    exam_mode = data["mode"]
    subject_id = data["subject_id"]

    # validate the mode of the exam
    if exam_mode not in ExamModes.get_valid_exam_modes():
        return bad_request(f"{exam_mode} is not in valid modes: {ExamModes.get_valid_exam_modes()}.")

    # get the student level for the particular subject
    student = student_manager.get_student_by_id(get_current_user()["user_id"])
    student_level = stusublvl_manager.get_student_subject_level(student.id, subject_id)
    if not student_level:
        student_level = stusublvl_manager.init_student_subject_level(student.id, subject_id)


    # validate the level of the student whether they can take that
    if student and not TestService.is_mode_accessible(exam_mode, student_level):
        return bad_request(f"{exam_mode} is not available at your current level!")
    
    
    questions = TestService.generate_random_questions_by_level(subject_id, student_level)
    questions = [question.to_json(include_correct_answer=False) for question in questions]

    # determine the number of points and total score
    total_points = TestService.determine_toal_test_points(questions)


    # create the test
    new_test = test_manager.create_test(
        student_id=student.id,
        questions=questions,
        total_points=total_points,
        total_score=len(questions),
        question_number=len(questions),
        school_id=student.school_id
    )

    return success_response(data=new_test.to_json(), status_code=201)


@testr.put("/tests/<int:test_id>/mark/")
def mark_test(test_id, json_data):
    return success_response()