from apiflask import APIBlueprint

from app._shared.schemas import UserTypes
from app._shared.api_errors import success_response
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.analytics.schemas import Responses, Requests
from app.analytics.operations import ssm_manager, ssr_manager

from app.admin.operations import topic_manager, subject_manager


analytics = APIBlueprint("analytics", __name__)


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


@analytics.get("/students/topic-performance/")
@analytics.input(Requests.TopicPerformanceQuerySchema, location="query")
@analytics.output(Responses.TopicPerformanceSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def topic_performance(query_data):

    student_id, subject_id = query_data.get("student_id", None), query_data.get(
        "subject_id", None
    )
    results = ssr_manager.get_topic_performance(
        student_id=student_id, subject_id=subject_id
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
