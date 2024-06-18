from app.extensions import db
from app._shared.models import BaseModel


# Association table for many-to-many relationship
student_batches = db.Table('student_batches',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('batch_id', db.Integer, db.ForeignKey('batch.id'), primary_key=True)
)


class Batch(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    batch_name = db.Column(db.String, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    curriculum = db.Column(db.String, nullable=False)
    students = db.relationship('Student', secondary=student_batches, backref=db.backref('batches', lazy=True))

    __table_args__ = (db.UniqueConstraint('batch_name', 'school_id', name='uix_batch_name_school_id'),)

    def to_json(self):
        return {
            'id': self.id,
            'batch_name': self.batch_name,
            'school_id': self.school_id,
            'curriculum': self.curriculum,
            'students': [student.to_json() for student in self.students]
        }
    


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
            'school_id': self.school_id,
            'is_approved': self.is_approved,
            'is_archived': self.is_archived
        }
    

