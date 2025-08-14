from apiflask import APIBlueprint

from app._shared.schemas import UserTypes
from app._shared.api_errors import success_response
from app._shared.decorators import token_auth, require_params_by_usertype
from app._shared.services import get_current_user

from app.analytics.schemas import Responses, Requests
from app.analytics.operations import ssm_manager, ssr_manager, sts_manager
from app.analytics.services import analytics_service


from app.app_admin.operations import topic_manager, subject_manager
from app.student.operations import student_manager, batch_manager

analytics = APIBlueprint("analytics", __name__)


#region NEW ANALYTICS

@analytics.get("/analytics/practice-rate")
@analytics.input(Requests.RateDistributionQuerySchema, location="query")
@analytics.output(Responses.PracticeRateDataSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id", "subject_id"]})
def practice_rate(query_data):
    school_id = get_current_user()["school_id"]
    practice_rate_results = analytics_service.get_practice_rate(school_id, **query_data)
    return success_response(data=practice_rate_results)


@analytics.get("/analytics/performance-distribution")
@analytics.input(Requests.RateDistributionQuerySchema, location="query")
@analytics.output(Responses.PerformanceDistributionDataSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id", "subject_id"]})
def performance_distribution(query_data):
    school_id = get_current_user()["school_id"]
    performance_distribution_results = analytics_service.get_performance_distribution(school_id, **query_data)
    return success_response(data=performance_distribution_results)






#region OLD ANALYTICS
@analytics.get("/students/dashboard/weekly-report/")
@analytics.output(Responses.WeeklyReportSchema)
@token_auth([UserTypes.student])
def weekly_report():
    student_id = get_current_user()["user_id"]
    last_week_time, this_week_time = ssm_manager.compare_session(student_id)
    difference = (
        round(((this_week_time - last_week_time) / last_week_time) * 100, 1)
        if last_week_time
        else 0
    )
    return success_response(
        data={"hours_spent": this_week_time, "percentage": difference}
    )


#TODO: add the checks and balances so people can't get data that does not belong to them

@analytics.get("/students/topic-performance/")
@analytics.input(Requests.TopicPerformanceQuerySchema, location="query")
@analytics.output(Responses.TopicPerformanceSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def topic_performance(query_data):

    student_id, subject_id = query_data.get("student_id", None), query_data.get(
        "subject_id", None
    )
    school_id = get_current_user()["school_id"]
    results = ssr_manager.get_topic_performance(
        student_id=student_id, subject_id=subject_id, school_id=school_id
    )

    performance = [
        {
            "topic_name": topic_manager.get_topic_by_id(topic_id).name,
            "subject_name": subject_manager.get_subject_by_id(subject_id).name,
            "low_count": low_count,
            "moderate_count": moderate_count,
            "high_count": high_count,
        }
        for topic_id, subject_id, low_count, moderate_count, high_count in results
    ]

    # Determine the best and worst-performing topics
    best_performing = sorted(performance, key=lambda x: x["high_count"], reverse=True)[
        :2
    ]
    worst_performing = sorted(performance, key=lambda x: x["low_count"], reverse=True)[
        :2
    ]
    return success_response(
        data={
            "best_performing_topics": best_performing,
            "worst_performing_topics": worst_performing,
        }
    )


@analytics.get("/student-performance/")
@analytics.input(Requests.TopicPerformanceQuerySchema, location="query")
@analytics.output(Responses.StudentPerformanceSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def student_performance(query_data):
    '''
    Get the general performance of the students in the school
    Query params:
    - student_id: int, optional, the id of the student to get performance for
    - subject_id: int, optional, the id of the subject to get performance for
    - batch_id: int, optional, the id of the batch to get performance for

    If the query params are not provided, the performance of all students in the school is returned.

    Returns:
    - performance: dict, the performance of the students in the school
    '''

    school_id = get_current_user()["school_id"]
    subject_id = query_data.get("subject_id", None)
    batch_id = query_data.get("batch_id", None)

    ## we need to get the students in the school or batch
    if batch_id:
        batch = batch_manager.get_batch_by_id(batch_id)
        students = batch.to_json()["students"]
        student_ids = [student["id"] for student in students]
    else:
        students = student_manager.get_active_students_by_school(school_id)
        student_ids = [student.id for student in students]

    results = sts_manager.get_score_distribution(
        total_students=len(students), subject_id=subject_id, student_ids=student_ids
    )
    return success_response(data=results)


@analytics.get("/performance-summary/")
@analytics.input(Requests.TopicPerformanceQuerySchema, location="query")
@analytics.output(Responses.PerformanceSummarySchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def performance_summary(query_data):
    school_id = get_current_user()["school_id"]
    subject_id = query_data.get("subject_id", None)
    batch_id = query_data.get("batch_id", None)

    if batch_id:
        batch = batch_manager.get_batch_by_id(batch_id)
        students = batch.to_json()["students"]
        student_ids = [student["id"] for student in students]
    else:
        students = student_manager.get_active_students_by_school(school_id)
        student_ids = [student.id for student in students]

    performance = sts_manager.get_average_and_failing_students_and_tests_completion(
       subject_id=subject_id, student_ids=student_ids
    )
    return success_response(data=performance)


@analytics.get("/topic-mastery/")
@analytics.input(Requests.TopicPerformanceQuerySchema, location="query")
@analytics.output(Responses.TopicMasteryDataSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def topic_mastery(query_data):
    school_id = get_current_user()["school_id"]
    subject_id = query_data.get("subject_id", None)
    batch_id = query_data.get("batch_id", None)

    if batch_id:
        batch = batch_manager.get_batch_by_id(batch_id)
        students = batch.to_json()["students"]
        student_ids = [student["id"] for student in students]
    else:
        students = student_manager.get_active_students_by_school(school_id)
        student_ids = [student.id for student in students]

    performance = sts_manager.get_top_and_bottom_topics(
        subject_id=subject_id, student_ids=student_ids
    )

    for topic in performance["strong_topics"]:
        topic["topic_name"] = topic_manager.get_topic_by_id(topic["topic_id"]).name

    for topic in performance["weak_topics"]:
        topic["topic_name"] = topic_manager.get_topic_by_id(topic["topic_id"]).name

    return success_response(data=performance)