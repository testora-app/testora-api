from app.extensions import db
from app._shared.models import BaseModel


# Association table for many-to-many relationship
staff_batches = db.Table('staff_batches',
    db.Column('staff_id', db.Integer, db.ForeignKey('staff.id'), primary_key=True),
    db.Column('batch_id', db.Integer, db.ForeignKey('batch.id'), primary_key=True)
)

staff_subjects = db.Table('staff_subjects',
    db.Column('staff_id', db.Integer, db.ForeignKey('staff.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True)
)

class Staff(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    other_names = db.Column(db.String, nullable=True)
    surname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, nullable=False)

    subjects = db.relationship('Subject', secondary=staff_subjects, back_populates='staff')

    def __repr__(self):
        return f'Staff {self.first_name} {self.surname}'

    def to_json(self, include_batches=False):
        data = {
            'id': self.id,
            'first_name': self.first_name,
            'other_names': self.other_names,
            'surname': self.surname,
            'email': self.email,
            'school_id': self.school_id,
            'is_approved': self.is_approved,
            'is_admin': self.is_admin,
            'subjects': [subject.to_json() for subject in self.subjects],
        }
        if include_batches:
            data['batches'] = [batch.to_json() for batch in self.batches] if self.batches else []
        return data
