from app.extensions import db, admin
from app._shared.models import BaseModel
from flask_admin.contrib.sqla import ModelView


class School(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    short_name = db.Column(db.String(11), nullable=False)
    logo = db.Column(db.String, nullable=True)
    location = db.Column(db.String, nullable=False)
    is_package_school = db.Column(
        db.Boolean, default=False
    )  # this we used to track default schools we put the solo students in
    phone_number = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    code = db.Column(db.String, nullable=False, unique=True)
    subscription_package = db.Column(db.String, nullable=True, default="Free")
    subscription_expiry_date = db.Column(db.Date, nullable=True, default=None)

    # --- New subscription manager fields (seat-based) ---
    # Canonical internal tier name: free|premium|premium_plus
    subscription_tier = db.Column(db.String(32), nullable=False, default="free")
    billing_cycle = db.Column(db.String(16), nullable=True, default=None)
    total_seats = db.Column(db.Integer, nullable=False, default=10)
    price_per_seat = db.Column(db.Float, nullable=False, default=0)
    scheduled_seat_reduction = db.Column(db.Integer, nullable=True, default=None)
    scheduled_reduction_date = db.Column(db.Date, nullable=True, default=None)
    scheduled_downgrade = db.Column(db.Boolean, nullable=False, default=False)
    scheduled_downgrade_date = db.Column(db.Date, nullable=True, default=None)
    scheduled_billing_cycle = db.Column(db.String(20), nullable=True, default=None)
    scheduled_billing_cycle_date = db.Column(db.Date, nullable=True, default=None)
    is_suspended = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"School {self.name}"

    def to_json(self):
        packages = {
            "free": {
                "name": "Free Plan",
                "description": "You have access to basic features with limited student capacity and standard support.",
            },
            "premium": {
                "name": "Premium Plan",
                "description": "You have full access to advanced analytics, unlimited student capacity, and dedicated support for your institution.",
            }
        }
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "logo": self.logo,
            "location": self.location,
            "phone_number": self.phone_number,
            "email": self.email,
            "code": self.code,
            "subscription_package": packages[self.subscription_package]["name"],
            "subscription_expiry_date": (
                str(self.subscription_expiry_date.strftime("%d %b %Y"))
                if self.subscription_expiry_date
                else self.subscription_expiry_date
            ),
            "subscription_package_description": packages[self.subscription_package]["description"],
            "is_suspended": self.is_suspended,

            # expose new subscription fields for the new subscription manager
            "subscription_tier": self.subscription_tier,
            "billing_cycle": self.billing_cycle,
            "total_seats": self.total_seats,
            "price_per_seat": self.price_per_seat,
            "scheduled_seat_reduction": self.scheduled_seat_reduction,
            "scheduled_reduction_date": (
                str(self.scheduled_reduction_date) if self.scheduled_reduction_date else None
            ),
            "scheduled_downgrade": self.scheduled_downgrade,
            "scheduled_downgrade_date": (
                str(self.scheduled_downgrade_date) if self.scheduled_downgrade_date else None
            ),
            "scheduled_billing_cycle": self.scheduled_billing_cycle,
            "scheduled_billing_cycle_date": (
                str(self.scheduled_billing_cycle_date) if self.scheduled_billing_cycle_date else None
            ),
        }


# admin.add_view(ModelView(School, db.session, name="Schools"))
