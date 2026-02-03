from typing import Dict
from datetime import datetime, timezone
from apiflask import APIBlueprint
from flask import render_template
from logging import info as log_info

from app._shared.schemas import SuccessMessage, UserTypes, ExamModes
from app._shared.api_errors import (
    success_response,
    bad_request,
    not_found,
    premium_only_feature,
)
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.app_admin.operations import subject_manager

from app.test.operations import question_manager, test_manager
from app.test.schemas import (
    TestQuestionsListSchema,
    QuestionListSchema,
    TestListSchema,
    TestQuerySchema,
    Responses,
    Requests,
)
from app.test.services import TestService

from app.student.operations import student_manager, stusublvl_manager
from app.student.services import SubjectLevelManager
from app.school.operations import school_manager
from app.subscriptions.constants import SubscriptionPackages, SubscriptionLimits, Features, FeatureStatus
from app.notifications.operations import recipient_manager


from app.analytics.topic_analytics import TopicAnalytics
from app.analytics.remarks_analyzer import RemarksAnalyzer
from app.achievements.services import AchievementEngine
from app.integrations.pusher import pusher
from app.integrations.mailer import mailer

import json


testr = APIBlueprint("testr", __name__)

# region questions


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
    sub = json_data.pop("sub_questions") if json_data.get("sub_questions", None) else []
    new_question = question_manager.create_question(**json_data)

    if sub:
        for s in sub:
            question_manager.create_subquestion(parent_question_id=new_question.id, **s)
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


@testr.post("/flag-questions/")
@testr.input(Requests.FlagQuestionSchema)
@testr.output(SuccessMessage)
def flag_questions(json_data):
    data = json_data["data"]
    question_ids = [q["question_id"] for q in data]

    objects = {q["question_id"]: q["flag_reason"] for q in data}

    questions = question_manager.get_question_by_ids(question_ids)

    for question in questions:
        question.is_flagged = True
        question.flag_reason = json.dumps(objects[question.id])
        question.save()


    html = render_template("flagged_questions.html", questions=questions)
    # send notification to admins here
    mailer.send_email(
        subject="Flagged Questions Notification",
        recipients=["support@preppee.online", "sg.apawu@gmail.com", "jaytaser@gmail.com"],
        text=html,
        html=True,
    )

    return success_response()


# endregion questions


# region Tests
@testr.get("/tests/")
@testr.input(TestQuerySchema, location="query")
@testr.output(TestListSchema)
@token_auth(["*"])
def test_history(query_data: Dict):
    current_user = get_current_user()

    if current_user["user_type"] == UserTypes.student:
        tests = test_manager.get_tests_by_student_ids([current_user["user_id"]])
    elif (
        current_user["user_type"] == UserTypes.staff
        or current_user["user_type"] == UserTypes.school_admin
    ):
        if query_data.get("student_id", None) is not None:
            tests = test_manager.get_tests_by_student_ids([query_data["student_id"]])
        else:
            tests = test_manager.get_tests_by_school_id(current_user["school_id"])
    else:
        tests = test_manager.get_tests()

    subject_ids = [test.subject_id for test in tests]

    subjects = subject_manager.get_subjects_by_ids(subject_ids)

    subjects = {subject.id: subject for subject in subjects}

    tests = [test.to_json() for test in tests]
    for test in tests:
        test["subject_name"] = subjects[test["subject_id"]].to_json()["name"]

    return success_response(data=tests)


@testr.post("/tests/")
@testr.input(Requests.CreateTestSchema)
@testr.output(Responses.TestSchema, 201)
@token_auth([UserTypes.student])
def create_test(json_data):
    """Returns the questions back to the user"""
    data = json_data["data"]
    exam_mode = data["mode"]
    subject_id = data["subject_id"]

    ## check if the school can take the subject they're requesting for
    school = school_manager.get_school_by_id(get_current_user()["school_id"])

    # get the name of the course, check if it's in the school's subscription thingy or not
    subject = subject_manager.get_subject_by_id(subject_id)

    if subject.is_premium and school.subscription_package != SubscriptionPackages.premium:
        return premium_only_feature()

    # validate the mode of the exam
    if exam_mode not in ExamModes.get_valid_exam_modes():
        return bad_request(
            f"{exam_mode} is not in valid modes: {ExamModes.get_valid_exam_modes()}."
        )

    if (
        SubscriptionLimits.get_limits(school.subscription_package)[Features.ExamMode]
        == FeatureStatus.DISABLED
    ):
        return premium_only_feature()

    # get the student level for the particular subject
    student = student_manager.get_student_by_id(get_current_user()["user_id"])
    student_level = stusublvl_manager.get_student_subject_level(student.id, subject_id)
    if not student_level:
        student_level = stusublvl_manager.init_student_subject_level(
            student.id, subject_id
        )

    # validate the level of the student whether they can take that
    if student and not TestService.is_mode_accessible(exam_mode, student_level.level):
        return bad_request(f"{exam_mode} mode is not available at your current level!")

    questions = TestService.generate_adaptive_questions(
        subject_id, student.id, student_level.level
    )
    questions = [
        question.to_json(include_correct_answer=False) for question in questions
    ]

    # determine the number of points and total score
    total_points = TestService.determine_total_test_points(questions)

    # number of questions should include sub questions

    # create the test
    new_test = test_manager.create_test(
        student_id=student.id,
        subject_id=subject_id,
        questions=questions,
        total_points=total_points,
        question_number=len(questions),
        school_id=student.school_id,
    )

    test_obj = new_test.to_json()
    test_obj["duration"] = TestService.determine_test_duration_in_seconds(
        subject.max_duration, len(questions)
    )

    return success_response(data=test_obj, status_code=201)


@testr.put("/tests/<int:test_id>/mark/")
@testr.input(Requests.MarkTestSchema)
@testr.output(SuccessMessage, 200)
@token_auth([UserTypes.student])
def mark_test(test_id, json_data):
    json_data = json_data["data"]
    test = test_manager.get_test_by_id(test_id)
    student = get_current_user()

    student_id = student["user_id"]

    if not test:
        return not_found(message="The requested Test does not exist!")

    if test:
        test.is_completed = True
        # TODO: Determine the level that'll deduct points

        marked_test = TestService.mark_test(json_data["questions"])
        # update the questions with the correct answer, it'll already have their answer
        test.finished_on = datetime.now(timezone.utc)
        test.meta = json_data["meta"]
        test.questions = marked_test["questions"]
        test.questions_correct = marked_test["score_acquired"]
        test.points_acquired = marked_test["points_acquired"]
        test.score_acquired = marked_test["score_acquired"]
        test.save()

        # update their points
        stusublvl = stusublvl_manager.get_student_subject_level(
            student_id, test.subject_id
        )
        stusublvl.points += marked_test["score_acquired"]
        stusublvl.save()

        last_test = test_manager.get_last_test_by_student_id(
            student_id, test.subject_id
        )
        # pass the sublvl to a level manager, that'll check if they've levelled up
        # and then add the history accordingly
        SubjectLevelManager.check_and_level_up(stu_sub_level=stusublvl)

        log_info("Running analytics...")
        # adding topic_scores
        # TODO: probably pass the test metadata here and then handle saving it here when they all return their responses
        TopicAnalytics.save_topic_scores_for_student(
            student_id, test.subject_id, test.id, marked_test["topic_scores"], marked_test["topic_totals"]
        )
        TopicAnalytics.test_level_topic_analytics(test.id, marked_test["topic_scores"], marked_test["topic_totals"])
        TopicAnalytics.student_level_topic_analytics(student_id, test.subject_id)
        RemarksAnalyzer.add_remarks_to_test(test, last_test)

        test_count = len(test_manager.get_tests_by_student_ids([student_id]))

        engine = AchievementEngine(student_id)
        engine.check_test_achievements(test.subject_id, test.score_acquired, test_count, email=student["user_email"])
        engine.check_level_achievements(email=student["user_email"])

        streak_update = student_manager.update_streak(student_id, datetime.now(timezone.utc))

        if streak_update["streak_modified"]:
            recipient = recipient_manager.get_recipient_by_email(
                student["user_email"], UserTypes.student
            )
            if recipient:
                pusher.notify_devices(
                    title=streak_update["message"]["title"],
                    content=streak_update["message"]["content"],
                    device_ids=recipient.device_ids,
                )

        # Update weekly goals
        try:
            from app.goals.services import UpdateWeeklyGoalsService
            import pytz
            
            # Get current date in Africa/Accra timezone
            accra_tz = pytz.timezone('Africa/Accra')
            current_date = datetime.now(accra_tz).date()
            
            # Get student's current streak
            student_obj = student_manager.get_student_by_id(student_id)
            
            # Update weekly goals using the service
            update_service = UpdateWeeklyGoalsService()
            result = update_service.run(
                student_id=student_id,
                current_date=current_date,
                subject_id=test.subject_id,
                xp_earned=marked_test["score_acquired"],
                current_streak=student_obj.current_streak if student_obj else 0
            )
            
            if result["updated"]:
                log_info(f"Weekly goals update: {result['message']}")
            else:
                log_info(f"Weekly goals not updated: {result['message']}")
                
        except Exception as e:
            # Log error but don't fail the test marking
            from logging import error as log_error
            log_error(f"Error updating weekly goals for student {student_id}: {str(e)}")

        log_info("Analytics ran successfully...")

    return success_response(data=test.to_json())


# endregion Tests
@testr.get("/tests/subject-performance/")
@testr.output(Responses.SubjectPerformances, 200)
@token_auth([UserTypes.school_admin, UserTypes.staff])
def subject_performance():
    school_id = get_current_user()["school_id"]
    students = student_manager.get_active_students_by_school(school_id)
    student_ids = [student.id for student in students]
    test_performances = test_manager.get_average_test_scores(student_ids=student_ids)

    average_scores = [
        {"subject_id": subject_id, "average_score": round(average_score, 2)}
        for subject_id, average_score in test_performances if test_performances
    ]

    if not average_scores:
        return success_response(data={"best_performing_subjects": [], "worst_performing_subjects": []})


    # Sort scores to identify best and worst performing subjects
    sorted_scores = sorted(
        average_scores, key=lambda x: x["average_score"], reverse=True
    )

    best_performing_subjects = sorted_scores[:1] 
    worst_performing_subjects = sorted_scores[-3:]

    best_performing = [
        {
            "subject_id": subject["subject_id"],
            "subject_name": subject_manager.get_subject_by_id(
                subject["subject_id"]
            ).short_name,
            "average_score": subject["average_score"],
        }
        for subject in best_performing_subjects
    ]

    worst_performing = [
        {
            "subject_id": subject["subject_id"],
            "subject_name": subject_manager.get_subject_by_id(
                subject["subject_id"]
            ).short_name,
            "average_score": subject["average_score"],
        }
        for subject in worst_performing_subjects
    ]

    return success_response(
        data={
            "best_performing_subjects": best_performing,
            "worst_performing_subjects": worst_performing,
        }
    )
