from apiflask import APIBlueprint
from flask import request
from datetime import datetime, timezone, timedelta

from app._shared.schemas import SuccessMessage, UserTypes
from app._shared.services import get_current_user
from app._shared.api_errors import  success_response, permissioned_denied, not_found, response_builder, bad_request
from app._shared.decorators import token_auth

from app.integrations.paystack import paystack

from app.subscriptions.schemas import Responses
from app.subscriptions.operations import sb_history_manager
from app.subscriptions.services import run_billing_process
from app.subscriptions.constants import PaymentStatus

from app.school.operations import school_manager

from globals import APP_SECRET_KEY


subscription = APIBlueprint('subscription', __name__)


@subscription.get('/billing-history/')
@subscription.output(Responses.SchoolBillingHistorySchema, 200)
@token_auth([UserTypes.school_admin])
def get_school_billing_history():
    school_id = get_current_user()['school_id']
    billing_history = sb_history_manager.get_school_billing_history(school_id)
    return success_response(data= [bill.to_json() for bill in billing_history])


# an endpoint to get a single billing
@subscription.get('/billing-history/<int:billing_id>/')
@subscription.output(Responses.SingleSchoolBillingHistorySchema, 200)
@token_auth([UserTypes.school_admin])
def get_single_billing_history(billing_id):
    
    school_id = get_current_user()['school_id']
    billing_history = sb_history_manager.get_school_billing_history_by_id(school_id, billing_id)
    return success_response(data= billing_history.to_json())

# an endpoint to settle the bill
@subscription.get('/billing-history/<int:billing_id>/settle/')
@subscription.output(Responses.PaymentInitSchema, 201)
@token_auth([UserTypes.school_admin])
def settle_billing_history(billing_id):
    school_id = get_current_user()['school_id']
    billing_history = sb_history_manager.get_school_billing_history_by_id(school_id, billing_id)

    if not billing_history:
        not_found('Bill not found')

    if billing_history.payment_status == PaymentStatus.success:
        return success_response(data= billing_history.to_json())
    
    user_email = get_current_user()['user_email']

    resp = paystack.create_payment(
        email=user_email,
        amount=billing_history.amount_due
    )

    if resp['status'] == True:
        billing_history.payment_reference = resp['data']['reference']
        billing_history.save()

        return success_response(data={
            "status": True,
            "authorization_url": resp['data']['authorization_url'],
            "reference": resp['data']['reference'],
            "access_code": resp['data']['access_code']
        })
    
    return response_builder(400, "Payment initialization failed")


# an endpoint to confirm payment
@subscription.get('/payment/<string:reference>/confirm/')
@subscription.output(Responses.SingleSchoolBillingHistorySchema, 200)
# @token_auth([UserTypes.school_admin])
def confirm_payment(reference):
    
    billing_history = sb_history_manager.get_school_billing_history_by_payment_ref(reference)

    if not billing_history:
        return not_found('Bill not found')

    if billing_history.payment_status == PaymentStatus.success:
        return success_response(data= billing_history.to_json())
    
    resp = paystack.verify_payment(billing_history.payment_reference)

    if resp['status'] == True:
        billing_history.payment_status = resp['data']['status']
        billing_history.settled_on = datetime.now(timezone.utc).date()
        billing_history.save()

        school = school_manager.get_school_by_id(billing_history.school_id)
        school.subscription_expiry_date = school.subscription_expiry_date + timedelta(days=31)
        school.save()

        return success_response(data=billing_history.to_json())
    
    return bad_request('Payment verification failed')


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


