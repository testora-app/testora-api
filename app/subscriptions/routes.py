import hashlib
import hmac

from apiflask import APIBlueprint
from flask import request
from datetime import datetime, timezone, timedelta

from app._shared.schemas import SuccessMessage, UserTypes
from app._shared.services import get_current_user
from app._shared.api_errors import (
    success_response,
    permissioned_denied,
    not_found,
    response_builder,
    bad_request,
)
from app._shared.decorators import token_auth

from app.integrations.paystack import paystack

from app.subscriptions.schemas import Responses, Requests
from app.subscriptions.operations import sb_history_manager
from app.subscriptions.services import run_billing_process
from app.subscriptions.constants import PaymentStatus, PackagePrices, SubscriptionPackages, TierNames, BillingCycles

from app.school.operations import school_manager

from globals import APP_SECRET_KEY, PAYSTACK_API_KEY


subscription = APIBlueprint("subscription", __name__)


# ---------------------------------------------------------------------------
# New Subscription Manager Endpoints (seat-based)
# ---------------------------------------------------------------------------


@subscription.get("/subscriptions/current")
@subscription.output(SuccessMessage, 200)
@token_auth([UserTypes.school_admin])
def get_current_subscription_plan():
    """Return the school's current seat-based subscription plan."""
    from app.subscriptions.subscription_manager import get_current_plan

    school_id = get_current_user()["school_id"]
    plan = get_current_plan(school_id)
    return success_response(data=plan.to_json())


@subscription.post("/subscriptions/add-seats")
@token_auth([UserTypes.school_admin])
def post_add_seats():
    """Add seats (requires payment first).

    Flow:
    1) Compute prorated amount
    2) Initialize Paystack transaction
    3) Persist pending billing history row with reference
    4) Frontend completes Paystack and then hits /payment/<ref>/confirm/ which
       finalizes the transaction and updates seats.
    """
    from app.subscriptions.subscription_manager import get_current_plan

    school_id = get_current_user()["school_id"]
    body = request.get_json() or {}
    data = body.get("data", body)
    seats_to_add = data.get("seats", None)
    if seats_to_add is None:
        return bad_request("'seats' is required")

    plan = get_current_plan(school_id)
    seats_to_add = int(seats_to_add)
    if plan.tier == TierNames.free:
        return bad_request("Cannot add seats on Free tier")
    if not plan.end_date or not plan.billing_cycle:
        return bad_request("Missing billing cycle/renewal date")

    # amount_due is prorated
    amount_due = PackagePrices.calculate_proration(
        tier=plan.tier,
        cycle=plan.billing_cycle,
        new_seats=seats_to_add,
        end_date=plan.end_date,
    )

    user_email = get_current_user()["user_email"]
    resp = paystack.create_payment(email=user_email, amount=amount_due)
    if resp.get("status") is True:
        ref = resp["data"]["reference"]

        # Persist a pending billing history record that encodes the seat change.
        # We store it as a special subscription_package string.
        now = datetime.now(timezone.utc).date()
        new_bill = sb_history_manager.add_school_billing_history(
            school_id=school_id,
            amount_due=amount_due,
            date_due=now,
            billed_on=now,
            settled_on=None,
            payment_reference=ref,
            subscription_package=f"add_seats:{seats_to_add}",
            subscription_start_date=now,
            subscription_end_date=plan.end_date,
        )
        new_bill.payment_status = PaymentStatus.pending
        new_bill.save()

        return success_response(
            data={
                "status": True,
                "authorization_url": resp["data"]["authorization_url"],
                "reference": ref,
                "access_code": resp["data"]["access_code"],
                "amount_due": amount_due,
            }
        )

    return response_builder(400, "Payment initialization failed")


@subscription.post("/subscriptions/schedule-reduction")
@token_auth([UserTypes.school_admin])
def post_schedule_reduction():
    """Schedule seat reduction for next renewal."""
    from app.subscriptions.subscription_manager import schedule_seat_reduction

    school_id = get_current_user()["school_id"]
    body = request.get_json() or {}
    data = body.get("data", body)
    seats_to_remove = data.get("seats", None)
    if seats_to_remove is None:
        return bad_request("'seats' is required")

    try:
        resp = schedule_seat_reduction(school_id, int(seats_to_remove))
    except ValueError as e:
        return bad_request(str(e))

    return success_response(data=resp)


@subscription.post("/subscriptions/schedule-downgrade")
@token_auth([UserTypes.school_admin])
def post_schedule_downgrade():
    """Schedule downgrade to Free tier for next renewal."""
    from app.subscriptions.subscription_manager import schedule_downgrade_to_free

    school_id = get_current_user()["school_id"]
    body = request.get_json() or {}
    data = body.get("data", body)
    confirm = data.get("confirmDowngrade")
    if confirm is not True:
        return bad_request("confirmDowngrade must be true")

    try:
        resp = schedule_downgrade_to_free(school_id)
    except ValueError as e:
        return bad_request(str(e))

    return success_response(data={"success": True, **resp})


@subscription.delete("/subscriptions/schedule-downgrade")
@token_auth([UserTypes.school_admin])
def delete_schedule_downgrade():
    """Cancel scheduled downgrade."""
    from app.subscriptions.subscription_manager import cancel_scheduled_downgrade

    school_id = get_current_user()["school_id"]
    cancel_scheduled_downgrade(school_id)
    return success_response(data={"success": True})


@subscription.post("/subscriptions/cancel-scheduled-change")
@token_auth([UserTypes.school_admin])
def post_cancel_scheduled_change():
    """Cancel any scheduled downgrade/reduction."""
    from app.subscriptions.subscription_manager import cancel_scheduled_changes

    school_id = get_current_user()["school_id"]
    resp = cancel_scheduled_changes(school_id)
    return success_response(data=resp)


@subscription.post("/subscriptions/schedule-cycle-change")
@token_auth([UserTypes.school_admin])
def post_schedule_cycle_change():
    """Schedule billing cycle change for next renewal.

    Request: { "data": { "new_cycle": "monthly" | "termly" | "yearly" } }
    """
    from app.subscriptions.subscription_manager import schedule_cycle_change

    school_id = get_current_user()["school_id"]
    body = request.get_json() or {}
    data = body.get("data", body)
    new_cycle = data.get("new_cycle", None)
    if new_cycle is None:
        return bad_request("'new_cycle' is required")

    try:
        resp = schedule_cycle_change(school_id, new_cycle)
    except ValueError as e:
        return bad_request(str(e))

    return success_response(data=resp)


@subscription.delete("/subscriptions/schedule-cycle-change")
@token_auth([UserTypes.school_admin])
def delete_schedule_cycle_change():
    """Cancel scheduled billing cycle change."""
    from app.subscriptions.subscription_manager import cancel_scheduled_cycle_change

    school_id = get_current_user()["school_id"]
    cancel_scheduled_cycle_change(school_id)
    return success_response(data={"success": True})


@subscription.get("/billing-history/")
@subscription.output(Responses.SchoolBillingHistorySchema, 200)
@token_auth([UserTypes.school_admin])
def get_school_billing_history():
    school_id = get_current_user()["school_id"]
    billing_history = sb_history_manager.get_school_billing_history(school_id)
    return success_response(data=[bill.to_json() for bill in billing_history])


@subscription.post("/billing-history/")
@subscription.input(Responses.SchoolBillingPostSchema)
@subscription.output(Responses.SchoolBillingHistorySchema, 201)
@token_auth([UserTypes.school_admin])
def add_billing_history(json_data):
    school_id = get_current_user()["school_id"]
    data = json_data["data"]

    now = datetime.now(timezone.utc).date()

    new_bill = sb_history_manager.add_school_billing_history(
        school_id=school_id,
        amount_due=data["amount_due"],
        date_due=now,
        billed_on=now,
        settled_on=now,
        payment_reference=data["payment_reference"],
        subscription_package=data["subscription_package"],
        subscription_start_date=now,
        subscription_end_date=now + timedelta(days=31),
    )
    return success_response(status_code=201, data=new_bill.to_json())


# an endpoint to get a single billing
@subscription.get("/billing-history/<int:billing_id>/")
@subscription.output(Responses.SingleSchoolBillingHistorySchema, 200)
@token_auth([UserTypes.school_admin])
def get_single_billing_history(billing_id):
    school_id = get_current_user()["school_id"]
    billing_history = sb_history_manager.get_school_billing_history_by_id(
        school_id, billing_id
    )
    return success_response(data=billing_history.to_json())


@subscription.post("/subscriptions/upgrade")
@token_auth([UserTypes.school_admin])
def post_upgrade():
    """Initiate a subscription upgrade (trial/free → premium/premium_plus).

    Request: { "data": { "tier": "premium", "billing_cycle": "termly", "seats": 50 } }
    """
    school_id = get_current_user()["school_id"]
    body = request.get_json() or {}
    data = body.get("data", body)

    tier = data.get("tier")
    billing_cycle = data.get("billing_cycle")
    seats = data.get("seats")

    valid_tiers = [TierNames.premium, TierNames.premium_plus]
    valid_cycles = [BillingCycles.monthly, BillingCycles.termly, BillingCycles.yearly]

    if tier not in valid_tiers:
        return bad_request(f"tier must be one of {valid_tiers}")
    if billing_cycle not in valid_cycles:
        return bad_request(f"billing_cycle must be one of {valid_cycles}")
    if not seats or int(seats) <= 0:
        return bad_request("seats must be > 0")

    school = school_manager.get_school_by_id(school_id)
    if school.subscription_tier == tier:
        return bad_request(
            "You are already on this tier. "
            "To add seats use /subscriptions/add-seats; "
            "to change your billing cycle use /subscriptions/schedule-cycle-change."
        )

    seats = int(seats)
    amount_due = PackagePrices.calculate_seat_total(tier, billing_cycle, seats)
    user_email = get_current_user()["user_email"]

    for stale in sb_history_manager.get_pending_upgrade_histories(school_id):
        stale.payment_status = PaymentStatus.failed
        stale.save()

    resp = paystack.create_payment(email=user_email, amount=amount_due)
    if resp.get("status") is True:
        ref = resp["data"]["reference"]
        now = datetime.now(timezone.utc).date()
        bill = sb_history_manager.add_school_billing_history(
            school_id=school_id,
            amount_due=amount_due,
            date_due=now,
            billed_on=now,
            settled_on=None,
            payment_reference=ref,
            subscription_package=f"upgrade:{tier}:{billing_cycle}:{seats}",
            subscription_start_date=now,
            subscription_end_date=now,
        )
        bill.payment_status = PaymentStatus.pending
        bill.save()
        return success_response(data={
            "authorization_url": resp["data"]["authorization_url"],
            "reference": ref,
            "access_code": resp["data"]["access_code"],
            "amount_due": amount_due,
        })
    return response_builder(400, "Payment initialization failed")


# an endpoint to settle the bill
@subscription.get("/billing-history/<int:billing_id>/settle/")
@subscription.output(Responses.PaymentInitSchema, 201)
@token_auth([UserTypes.school_admin])
def settle_billing_history(billing_id):
    school_id = get_current_user()["school_id"]
    billing_history = sb_history_manager.get_school_billing_history_by_id(
        school_id, billing_id
    )

    if not billing_history:
        not_found("Bill not found")

    if billing_history.payment_status == PaymentStatus.success:
        return success_response(data=billing_history.to_json())

    user_email = get_current_user()["user_email"]

    resp = paystack.create_payment(email=user_email, amount=billing_history.amount_due)

    if resp["status"] == True:
        billing_history.payment_reference = resp["data"]["reference"]
        billing_history.save()

        return success_response(
            status_code=201,
            data={
                "status": True,
                "authorization_url": resp["data"]["authorization_url"],
                "reference": resp["data"]["reference"],
                "access_code": resp["data"]["access_code"],
            }
        )

    return response_builder(400, "Payment initialization failed")


# an endpoint to confirm payment
@subscription.get("/payment/<string:reference>/confirm/")
@subscription.output(Responses.SingleSchoolBillingHistorySchema, 200)
@token_auth([UserTypes.school_admin])
def confirm_payment(reference):

    billing_history = sb_history_manager.get_school_billing_history_by_payment_ref(
        reference, lock=True
    )

    if not billing_history:
        return not_found("Bill not found")

    if billing_history.payment_status == PaymentStatus.success:
        return success_response(data=billing_history.to_json())

    resp = paystack.verify_payment(billing_history.payment_reference)

    if resp["status"] == True:
        billing_history.payment_status = resp["data"]["status"]
        billing_history.settled_on = datetime.now(timezone.utc).date()
        billing_history.save()

        school = school_manager.get_school_by_id(billing_history.school_id)

        pkg = str(billing_history.subscription_package or "")

        if pkg.startswith("add_seats:"):
            try:
                seats_to_add = int(pkg.split(":", 1)[1])
            except Exception:
                seats_to_add = 0

            if seats_to_add > 0:
                if school.subscription_tier == TierNames.trial:
                    if getattr(school, "scheduled_downgrade", False):
                        school.scheduled_downgrade = False
                        school.scheduled_downgrade_date = None
                elif getattr(school, "scheduled_downgrade", False):
                    return bad_request("Downgrade is scheduled. Cancel it before adding seats.")

                school.total_seats = int(school.total_seats or 0) + int(seats_to_add)
                school.save()
            return success_response(data=billing_history.to_json())

        elif pkg.startswith("upgrade:"):
            try:
                _, tier, billing_cycle, seats_str = pkg.split(":", 3)
                seats = int(seats_str)
            except Exception:
                return bad_request("Malformed upgrade record")
            from app.subscriptions.upgrade_handler import handle_successful_upgrade
            handle_successful_upgrade(school, tier, billing_cycle, seats)

        else:
            cycle = school.billing_cycle or BillingCycles.monthly
            cycle_days = PackagePrices.get_days_in_cycle(cycle)
            base = school.subscription_expiry_date or datetime.now(timezone.utc).date()
            school.subscription_expiry_date = base + timedelta(days=cycle_days)
            school.subscription_package = SubscriptionPackages.premium
            school.save()

        return success_response(data=billing_history.to_json())

    return bad_request("Payment verification failed")

@subscription.post("/paystack-webhook/")
@subscription.output(SuccessMessage, 200)
def paystack_webhook():
    signature = request.headers.get("X-Paystack-Signature", "")
    body = request.get_data()
    expected = hmac.new(
        PAYSTACK_API_KEY.encode("utf-8"), body, hashlib.sha512
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return permissioned_denied("Invalid webhook signature")

    event = request.get_json()
    event_type = event.get('event')

    billing_history = sb_history_manager.get_school_billing_history_by_payment_ref(
        event['data']['reference'], lock=True
    )

    if not billing_history:
        return not_found("Bill not found")

    # Example: handle successful payment
    if event_type == 'charge.success':

        if billing_history.payment_status == PaymentStatus.success:
            return success_response()
        
        billing_history.payment_status = PaymentStatus.success
        billing_history.settled_on = datetime.now(timezone.utc).date()
        billing_history.save()

        school = school_manager.get_school_by_id(billing_history.school_id)
        pkg = str(billing_history.subscription_package or "")

        if pkg.startswith("add_seats:"):
            try:
                seats_to_add = int(pkg.split(":", 1)[1])
            except Exception:
                seats_to_add = 0
            if seats_to_add > 0:
                school.total_seats = int(school.total_seats or 0) + seats_to_add
                school.save()

        elif pkg.startswith("upgrade:"):
            try:
                _, tier, billing_cycle, seats_str = pkg.split(":", 3)
                seats = int(seats_str)
            except Exception:
                seats = 0
            if seats > 0:
                from app.subscriptions.upgrade_handler import handle_successful_upgrade
                handle_successful_upgrade(school, tier, billing_cycle, seats)

        else:
            cycle = school.billing_cycle or BillingCycles.monthly
            cycle_days = PackagePrices.get_days_in_cycle(cycle)
            base = school.subscription_expiry_date or datetime.now(timezone.utc).date()
            school.subscription_expiry_date = base + timedelta(days=cycle_days)
            school.subscription_package = SubscriptionPackages.premium
            school.save()

    elif event_type == 'charge.failed':
        billing_history.payment_status = PaymentStatus.failed
        billing_history.save()
    
    return success_response()


# an endpoint that will be hit everyday to run billing process
@subscription.post("/billing-process/")
@subscription.output(SuccessMessage, 200)
def run_billing():
    auth_header = request.headers.get("X-Internal-Key", "")
    if not auth_header or not hmac.compare_digest(auth_header, APP_SECRET_KEY):
        return permissioned_denied()

    from app.subscriptions.subscription_manager import apply_renewal_if_due
    apply_renewal_if_due()
    run_billing_process()
    return success_response()


@subscription.post("/suspension-process/")
@subscription.output(SuccessMessage, 200)
def run_suspension():
    auth_header = request.headers.get("X-Internal-Key", "")
    if not auth_header or not hmac.compare_digest(auth_header, APP_SECRET_KEY):
        return permissioned_denied()

    from app.subscriptions.services import run_suspension_process
    run_suspension_process()
    return success_response()


@subscription.post("/renewal-process/")
@subscription.output(SuccessMessage, 200)
def run_renewal():
    auth_header = request.headers.get("X-Internal-Key", "")
    if not auth_header or not hmac.compare_digest(auth_header, APP_SECRET_KEY):
        return permissioned_denied()

    from app.subscriptions.subscription_manager import apply_renewal_if_due
    processed = apply_renewal_if_due()
    return success_response(data={"processed": processed})
