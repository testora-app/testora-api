from app.extensions import db
from app._shared.models import BaseModel

class School(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    short_name = db.Column(db.String(11), nullable=False)
    logo = db.Column(db.String, nullable=True)
    location = db.Column(db.String, nullable=False)
    is_package_school = db.Column(db.Boolean, default=False) # this we used to track default schools we put the solo students in
    phone_number = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    code = db.Column(db.String, nullable=False, unique=True)
    subscription_package = db.Column(db.String, nullable=True, default='free')
    subscription_expiry_date = db.Column(db.Date, nullable=True, default=None)
    is_suspended = db.Column(db.Boolean, default=False)


    def __repr__(self):
        return f'School {self.name}'

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'logo': self.logo,
            'location': self.location,
            'phone_number': self.phone_number,
            'email': self.email,
            'code': self.code,
            'subscription_package': self.subscription_package.title(),
            'subscription_expiry_date': str(self.subscription_expiry_date) if self.subscription_expiry_date else self.subscription_expiry_date,
            'is_suspended': self.is_suspended
        }