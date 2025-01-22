from apiflask import APIBlueprint

from app._shared.schemas import UserTypes
from app._shared.api_errors import success_response
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.achievements.schemas import Responses, Requests

achievements = APIBlueprint("achievements", __name__)


@achievements.get("/achievements/")
@achievements.input(Requests.AchievementReport, location="query")
@achievements.output(Responses.AchievementSchema)
@token_auth([UserTypes.student, UserTypes.school_admin, UserTypes.staff])
def get_student_achievements():
    return success_response(
        data=[]
    )

