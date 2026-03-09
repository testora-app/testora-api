from app._shared.operations import BaseManager

from app.subscriptions.models import SchoolBillingHistory
from app.subscriptions.constants import PaymentStatus

from typing import List


class SchoolBillingHistoryManager(BaseManager):

    def get_school_billing_history(self, school_id: int) -> List[SchoolBillingHistory]:
        return SchoolBillingHistory.query.filter_by(school_id=school_id).all()

    def get_school_billing_history_by_id(
        self, school_id: int, billing_history_id: int
    ) -> SchoolBillingHistory:
        return SchoolBillingHistory.query.filter_by(
            school_id=school_id, id=billing_history_id
        ).first()

    def get_school_billing_history_by_payment_ref(
        self, payment_reference: str, lock: bool = False
    ) -> SchoolBillingHistory:
        q = SchoolBillingHistory.query.filter_by(
            payment_reference=payment_reference, is_deleted=False
        )
        if lock:
            q = q.with_for_update()
        return q.first()

    def get_school_billing_history_by_subscription_expiry_date(
        self, school_id: int, subscription_expiry_date: str
    ) -> SchoolBillingHistory:
        return SchoolBillingHistory.query.filter_by(
            school_id=school_id,
            subscription_end_date=subscription_expiry_date,
            is_deleted=False,
        ).first()

    def get_pending_upgrade_histories(self, school_id: int) -> List[SchoolBillingHistory]:
        return SchoolBillingHistory.query.filter(
            SchoolBillingHistory.school_id == school_id,
            SchoolBillingHistory.payment_status == PaymentStatus.pending,
            SchoolBillingHistory.subscription_package.like("upgrade:%"),
            SchoolBillingHistory.is_deleted == False,
        ).all()

    def get_overdue_billing_histories(
        self, date_due: str
    ) -> List[SchoolBillingHistory]:
        return SchoolBillingHistory.query.filter(
            SchoolBillingHistory.date_due <= date_due,
            SchoolBillingHistory.payment_status == PaymentStatus.pending,
            SchoolBillingHistory.is_deleted == False,
        ).all()

    def add_school_billing_history(
        self,
        school_id,
        amount_due,
        date_due,
        billed_on,
        settled_on,
        payment_reference,
        subscription_package,
        subscription_start_date,
        subscription_end_date,
    ) -> SchoolBillingHistory:
        billing_history = SchoolBillingHistory(
            school_id=school_id,
            amount_due=amount_due,
            date_due=date_due,
            billed_on=billed_on,
            settled_on=settled_on,
            payment_reference=payment_reference,
            subscription_package=subscription_package,
            subscription_start_date=subscription_start_date,
            subscription_end_date=subscription_end_date,
            payment_status=PaymentStatus.pending,
        )

        self.save(billing_history)
        return billing_history


sb_history_manager = SchoolBillingHistoryManager()
