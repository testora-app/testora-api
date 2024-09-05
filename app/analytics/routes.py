from apiflask import APIBlueprint

from app._shared.schemas import UserTypes
from app._shared.api_errors import  success_response
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.analytics.schemas import Responses
from app.analytics.operations import ssm_manager


analytics = APIBlueprint('analytics', __name__)


@analytics.get('/students/dashboard/weekly-report/')
@analytics.output(Responses.WeeklyReportSchema)
@token_auth([UserTypes.student])
def weekly_report():
    student_id = get_current_user()['user_id']
    last_week_time, this_week_time = ssm_manager.compare_session(student_id)
    difference = round(((this_week_time - last_week_time)/ last_week_time) * 100, 1) if last_week_time else 0
    return success_response(data={'hours_spent': this_week_time, 'percentage': difference})