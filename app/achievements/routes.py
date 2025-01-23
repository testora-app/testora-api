from apiflask import APIBlueprint

from app._shared.schemas import UserTypes
from app._shared.api_errors import success_response
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.achievements.schemas import Responses, Requests
from app.achievements.operations import achievement_manager, student_has_achievement_manager

achievements = APIBlueprint("achievements", __name__)


@achievements.get("/achievements/")
@achievements.input(Requests.AchievementReport, location="query")
@achievements.output(Responses.AchievementResponseSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def get_student_achievements(query_data):
    student_achievements = student_has_achievement_manager.get_student_achievements(
        query_data["student_id"]
    )

    achievements = [achievement.to_json() for achievement in student_achievements]

    for student_achievement in achievements:
        student_achievement["achievement"] = achievement_manager.get_achievement(
            student_achievement["achievement_id"]
        ).to_json(include_requirements=False)
        student_achievement.pop("achievement_id")

    return success_response(
        data=achievements
    )

