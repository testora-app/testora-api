from app.subscriptions.operations import sb_history_manager
from app.subscriptions.constants import PackagePrices

from app.school.operations import school_manager
from app.student.operations import student_manager

from datetime import datetime, timezone, timedelta


def run_billing_process() -> None:
    schools = school_manager.get_schools_with_expired_subscriptions(datetime.now(timezone.utc).date())
    bill_data = []

    for school in schools:
        billing_history = sb_history_manager.get_school_billing_history_by_subscription_expiry_date(school.id, school.subscription_expiry_date)
        if billing_history:
            continue

        student_number = len(student_manager.get_active_students_by_school(school.id))
        new_bill = sb_history_manager.add_school_billing_history(
            school_id= school.id,
            amount_due= PackagePrices.calculate_subscription_price(school.subscription_package, student_number),
            date_due= (datetime.now(timezone.utc) + timedelta(days=7)).date(),
            billed_on= datetime.now(timezone.utc),
            settled_on= None,
            payment_reference= None,
            subscription_package= school.subscription_package,
            subscription_start_date= (datetime.now(timezone.utc) - timedelta(days=30)).date(),
            subscription_end_date= school.subscription_expiry_date
        )

        bill_data.append(new_bill)

    return bill_data
