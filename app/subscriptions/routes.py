from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes
from app._shared.services import get_current_user
from app._shared.api_errors import  success_response
from app._shared.decorators import token_auth

from app.subscriptions.schemas import Responses
from app.subscriptions.operations import sb_history_manager


subscription = APIBlueprint('subscription', __name__)


@subscription.get('/billing-history/')
@subscription.output(Responses.SchoolBillingHistorySchema, 200)
@token_auth([UserTypes.school_admin])
def get_school_billing_history():
    school_id = get_current_user()['school_id']
    billing_history = sb_history_manager.get_school_billing_history(school_id)
    return success_response(data= [bill.to_json() for bill in billing_history])