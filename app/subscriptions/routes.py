from apiflask import APIBlueprint
from flask import request

from app._shared.schemas import SuccessMessage, UserTypes
from app._shared.services import get_current_user
from app._shared.api_errors import  success_response, permissioned_denied
from app._shared.decorators import token_auth

from app.subscriptions.schemas import Responses
from app.subscriptions.operations import sb_history_manager
from app.subscriptions.services import run_billing_process

from globals import APP_SECRET_KEY


subscription = APIBlueprint('subscription', __name__)


@subscription.get('/billing-history/')
@subscription.output(Responses.SchoolBillingHistorySchema, 200)
@token_auth([UserTypes.school_admin])
def get_school_billing_history():
    school_id = get_current_user()['school_id']
    billing_history = sb_history_manager.get_school_billing_history(school_id)
    return success_response(data= [bill.to_json() for bill in billing_history])


# an endpoint that will be hit everyday to run billing process
@subscription.get('/billing-process/')
@subscription.output(SuccessMessage, 200)
def run_billing():
    code = request.args.get('code')
    if not code:
        return permissioned_denied()
    
    if code == APP_SECRET_KEY:
        bill_data = run_billing_process()
    else:
        return permissioned_denied()

    # send them notification/email
    return success_response()


