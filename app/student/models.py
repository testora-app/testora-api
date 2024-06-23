from app.extensions import db
from app._shared.models import BaseModel

from datetime import datetime

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

    def to_json(self, include_students=True):
        data = {
            'id': self.id,
            'batch_name': self.batch_name,
            'school_id': self.school_id,
            'curriculum': self.curriculum,
        }
        if include_students:
            data['students'] =  [student.to_json() for student in self.students]
        return data
    
    

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
            'is_archived': self.is_archived,
            'batches': [batch.to_json(include_students=False) for batch in self.batches] if self.batches else []
        }
    

class StudentSubjectLevel(BaseModel):
    __tablename__ = 'student_subject_level'

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), primary_key=True)
    level = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'level': self.level,
            'points': self.points
        }


class StudentLevellingHistory(BaseModel):
    __tablename__ = 'student_levelling_history'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    level_from = db.Column(db.Integer, nullable=False)
    level_to = db.Column(db.Integer, nullable=False)
    levelled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    meta = db.Column(db.JSON, nullable=True)

    def to_json(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'level_from': self.level_from,
            'level_to': self.level_to,
            'levelled_at': self.levelled_at,
            'metadata': self.metadata,
        }

