from app.extensions import db
from app._shared.models import BaseModel


class Student(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    other_names = db.Column(db.String, nullable=True)
    surname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'Staff {self.first_name} {self.surname}'

    def to_json(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'other_names': self.other_names,
            'surname': self.surname,
            'email': self.email,
            'password_hash': self.password_hash,
            'school_id': self.school_id,
            'is_approved': self.is_approved,
            'is_archived': self.is_archived
        }