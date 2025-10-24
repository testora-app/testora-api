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


@analytics.get("/analytics/subject-performance")
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.SubjectPerformanceDataSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id", "subject_id"]})
def subject_performance(query_data):
    school_id = get_current_user()["school_id"]
    subject_performance_results = analytics_service.get_subject_performance(school_id, **query_data)
    return success_response(data=subject_performance_results)


@analytics.get("/analytics/recent-tests-activities")
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.RecentTestActivitiesSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id", "subject_id"]})
def recent_tests_activities(query_data):
    school_id = get_current_user()["school_id"]
    recent_tests_activities_results = analytics_service.get_recent_tests_activities(school_id, **query_data)
    return success_response(data=recent_tests_activities_results)


@analytics.get("/analytics/proficiency-distribution")
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.ProficiencyDistributionDataSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id", "subject_id"]})
def proficiency_distribution(query_data):
    school_id = get_current_user()["school_id"]
    proficiency_distribution_results = analytics_service.get_proficiency_distribution(school_id, **query_data)
    return success_response(data=proficiency_distribution_results)


@analytics.get("/analytics/average-score-trend")
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.AverageScoreTrendSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id", "subject_id"]})
def average_score_trend(query_data):
    school_id = get_current_user()["school_id"]
    average_score_trend_results = analytics_service.get_average_score_trend(school_id, **query_data)
    return success_response(data=average_score_trend_results)


@analytics.get("/analytics/performance-general")
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.PerformanceGeneralDataSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id"]})
def performance_general(query_data):
    school_id = get_current_user()["school_id"]
    performance_general_results = analytics_service.get_performance_general(school_id, **query_data)
    return success_response(data=performance_general_results)


@analytics.get("/analytics/students-proficiency")
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.StudentsProficiencyDataSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id", "subject_id"]})
def students_proficiency(query_data):
    students_proficiency_results = analytics_service.get_students_proficiency(**query_data)
    return success_response(data=students_proficiency_results)


@analytics.get("/analytics/topic-level-breakdown")
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.TopicLevelBreakdownDataSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
@require_params_by_usertype({UserTypes.staff: ["batch_id", "subject_id"]})
def performance_topics(query_data):
    """
    Get mock performance data for topics.
    
    Optional query parameters:
    - stage: Filter by stage (e.g., "Stage 1-3", "Stage 4-6", "Stage 7-9")
    - level: Filter by proficiency level (e.g., "EMERGING", "DEVELOPING", "APPROACHING_PROFICIENT", "HIGHLY_PROFICIENT")
    
    Returns:
    - list of topic performance data
    """
    
    # Get optional query parameters

    
    # Call the service function with filters
    filtered_data = analytics_service.get_performance_topics(**query_data)
    
    return success_response(
        message="Performance topics retrieved successfully",
        data=filtered_data
    )


@analytics.get('/analytics/<student_id>/performance-indicators')
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.PerformanceIndicatorsDataSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def performance_indicators(student_id, query_data):
    performance_indicators_results = analytics_service.get_performance_indicators(student_id, **query_data)
    return success_response(data=performance_indicators_results)


@analytics.get('/analytics/<student_id>/subject-proficiency')
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.SubjectProficiencyDataSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def subject_proficiency(student_id, query_data):
    subject_proficiency_results = analytics_service.get_subject_proficiency(student_id, **query_data)
    return success_response(data=subject_proficiency_results)


@analytics.get('/analytics/<student_id>/test-history')
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.TestHistoryDataSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def test_history(student_id, query_data):
    test_history_results = analytics_service.get_test_history(student_id, **query_data)
    return success_response(data=test_history_results)


@analytics.get('/analytics/<student_id>/proficiency-graph')
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.ProficiencyGraphDataSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def proficiency_graph(student_id, query_data):
    proficiency_graph_results = analytics_service.get_proficiency_graph(student_id, **query_data)
    return success_response(data=proficiency_graph_results)


@analytics.get('/analytics/<student_id>/failing-topics')
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.FailingTopicsDataSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def failing_topics(student_id, query_data):
    failing_topics_results = analytics_service.get_failing_topics(student_id, **query_data)
    return success_response(data=failing_topics_results)


@analytics.get('/analytics/<student_id>/student-proficiency')
@analytics.input(Requests.AnalyticsQuerySchema, location="query")
@analytics.output(Responses.StudentProficiencyDataSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def student_proficiency(student_id, query_data):
    student_proficiency_results = analytics_service.get_student_average_and_band(student_id, **query_data)
    return success_response(data=student_proficiency_results)



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
