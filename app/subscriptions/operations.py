from app.extensions import db
from app._shared.operations import BaseManager

from app.subscriptions.models import SchoolBillingHistory

from typing import List


class SchoolBillingHistoryManager(BaseManager):
    
    def get_school_billing_history(self, school_id: int) -> List[SchoolBillingHistory]:
        return SchoolBillingHistory.query.filter_by(school_id=school_id).all()
    
    def get_school_billing_history_by_id(self, school_id: int, billing_history_id: int) -> SchoolBillingHistory:
        return SchoolBillingHistory.query.filter_by(school_id=school_id, id=billing_history_id).first()
    
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
        subscription_end_date=subscription_end_date
        )

        self.save(billing_history)
        return billing_history
    


sb_history_manager = SchoolBillingHistoryManager()
    
