from typing import Dict
from datetime import datetime
from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes, ExamModes
from app._shared.api_errors import  success_response, bad_request, not_found
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.test.operations import question_manager, test_manager
from app.test.schemas import TestQuestionsListSchema, QuestionListSchema, TestListSchema, Responses, Requests
from app.test.services import TestService

from app.student.operations import student_manager, stusublvl_manager
from app.student.services import SubjectLevelManager


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
    sub = json_data.pop('sub_questions') if json_data.get('sub_questions', None) else []
    new_question = question_manager.create_question(**json_data)
    
    if sub:
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


# region: Tests
@testr.get("/tests/")
@testr.output(TestListSchema)
@token_auth(['*'])
def test_history():
    current_user = get_current_user()

    if current_user['user_type'] == UserTypes.student:
        tests = test_manager.get_tests_by_student_ids([current_user['user_id']])
    elif current_user['user_type'] == UserTypes.staff or current_user['user_type'] == UserTypes.school_admin:
        tests = test_manager.get_tests_by_school_id(current_user['school_id'])
    else:
        tests = test_manager.get_tests()

    return success_response(data=[test.to_json() for test in tests])


@testr.post("/tests/")
@testr.input(Requests.CreateTestSchema)
@testr.output(Responses.TestSchema, 201)
@token_auth([UserTypes.student])
def create_test(json_data):
    ''' Returns the questions back to the user'''
    data = json_data["data"]
    exam_mode = data["mode"]
    subject_id = data["subject_id"]

    ## add a verfication layer to check if student takes that course

    # validate the mode of the exam
    if exam_mode not in ExamModes.get_valid_exam_modes():
        return bad_request(f"{exam_mode} is not in valid modes: {ExamModes.get_valid_exam_modes()}.")

    # get the student level for the particular subject
    student = student_manager.get_student_by_id(get_current_user()["user_id"])
    student_level = stusublvl_manager.get_student_subject_level(student.id, subject_id)
    if not student_level:
        student_level = stusublvl_manager.init_student_subject_level(student.id, subject_id)
        

    # validate the level of the student whether they can take that
    if student and not TestService.is_mode_accessible(exam_mode, student_level.level):
        return bad_request(f"{exam_mode} mode is not available at your current level!")
    
    
    questions = TestService.generate_random_questions_by_level(subject_id, student_level.level)
    questions = [question.to_json(include_correct_answer=False) for question in questions]

    # determine the number of points and total score
    total_points = TestService.determine_total_test_points(questions)


    # create the test
    new_test = test_manager.create_test(
        student_id=student.id,
        subject_id=subject_id,
        questions=questions,
        total_points=total_points,
        total_score=len(questions),
        question_number=len(questions),
        school_id=student.school_id
    )

    return success_response(data=new_test.to_json(), status_code=201)


@testr.put("/tests/<int:test_id>/mark/")
@testr.input(Requests.MarkTestSchema)
@testr.output(SuccessMessage, 200)
@token_auth([UserTypes.student])
def mark_test(test_id, json_data):
    json_data = json_data["data"]
    test = test_manager.get_test_by_id(test_id)
    student_id = get_current_user()['user_id']

    if not test:
        return not_found(message="The requested Test does not exist!")

    if test and not test.is_completed:
        test.is_completed = True
        #TODO: Determine the level that'll deduct points

        marked_test = TestService.mark_test(json_data['questions'])
        # update the questions with the correct answer, it'll already have their answer
        test.finished_on = datetime.utcnow()
        test.meta = json_data['meta']
        test.questions = marked_test['questions']
        test.questions_correct = marked_test['score_acquired']
        test.points_acquired = marked_test['points_acquired']
        test.score_acquired = marked_test['score_acquired']
        test.save()

        # update their points
        stusublvl = stusublvl_manager.get_student_subject_level(student_id, test.subject_id)
        stusublvl.points += marked_test['score_acquired']
        stusublvl.save()

        # pass the sublvl to a level manager, that'll check if they've levelled up
        # and then add the history accordingly
        SubjectLevelManager.check_and_level_up(stu_sub_level=stusublvl)
    return success_response(data=test.to_json())


# endregion: Tests