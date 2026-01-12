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
    is_suspended = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"School {self.name}"

    def to_json(self):
        packages = {
            "Free": {
                "name": "Free Plan",
                "description": "You have access to basic features with limited student capacity and standard support.",
            },
            "Premium": {
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
        }


# admin.add_view(ModelView(School, db.session, name="Schools"))
