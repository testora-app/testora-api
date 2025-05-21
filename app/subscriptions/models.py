from app.extensions import db, admin
from app._shared.models import BaseModel

from app.subscriptions.constants import PaymentStatus

from flask_admin.contrib.sqla import ModelView


class SchoolBillingHistory(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    amount_due = db.Column(db.Float, nullable=False)
    date_due = db.Column(db.Date, nullable=False)
    billed_on = db.Column(db.Date, nullable=False)
    settled_on = db.Column(db.Date, nullable=True, default=None)
    payment_reference = db.Column(db.String(200), default=None, nullable=True)
    payment_status = db.Column(
        db.String(100),
        nullable=True,
        default=PaymentStatus.pending,
        server_default=PaymentStatus.pending,
    )
    subscription_package = db.Column(db.String(100), nullable=False)
    subscription_start_date = db.Column(db.Date, nullable=False)
    subscription_end_date = db.Column(db.Date, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "school_id": self.school_id,
            "amount_due": self.amount_due,
            "date_due": str(self.date_due) if self.date_due else None,
            "billed_on": str(self.billed_on) if self.billed_on else None,
            "settled_on": str(self.settled_on) if self.settled_on else None,
            "payment_reference": self.payment_reference,
            "subscription_package": self.subscription_package,
            "subscription_start_date": (
                str(self.subscription_start_date)
                if self.subscription_start_date
                else None
            ),
            "subscription_end_date": (
                str(self.subscription_end_date) if self.subscription_end_date else None
            ),
            "payment_status": self.payment_status,
        }


admin.add_view(ModelView(SchoolBillingHistory, db.session, name="BillingHistory"))
