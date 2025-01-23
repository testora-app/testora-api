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
@achievements.output(Responses.AchievementSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def get_student_achievements(query_data):
    return success_response(
        data=[]
    )

