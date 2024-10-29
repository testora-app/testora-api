from app._shared.operations import BaseManager

from app.subscriptions.models import SchoolBillingHistory
from app.subscriptions.constants import PaymentStatus

from typing import List


class SchoolBillingHistoryManager(BaseManager):
    
    def get_school_billing_history(self, school_id: int) -> List[SchoolBillingHistory]:
        return SchoolBillingHistory.query.filter_by(school_id=school_id).all()
    
    def get_school_billing_history_by_id(self, school_id: int, billing_history_id: int) -> SchoolBillingHistory:
        return SchoolBillingHistory.query.filter_by(school_id=school_id, id=billing_history_id).first()
    
    def get_school_billing_history_by_payment_ref(self, school_id: int, payment_reference: str) -> SchoolBillingHistory:
        return SchoolBillingHistory.query.filter_by(school_id=school_id, payment_reference=payment_reference, is_deleted=False).first()
    
    def get_school_billing_history_by_subscription_expiry_date(self, school_id: int, subscription_expiry_date: str) -> SchoolBillingHistory:
        return SchoolBillingHistory.query.filter_by(school_id=school_id, subscription_expiry_date=subscription_expiry_date, is_deleted=False).first()
    
    def add_school_billing_history(self, school_id, amount_due, date_due, billed_on, settled_on, payment_reference, 
                                   subscription_package, subscription_start_date, subscription_end_date) -> SchoolBillingHistory:
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
        payment_status=PaymentStatus.pending
        )

        self.save(billing_history)
        return billing_history
    


sb_history_manager = SchoolBillingHistoryManager()
    
