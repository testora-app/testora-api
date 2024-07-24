from app.extensions import db
from app._shared.models import BaseModel


class StudentTopicScores(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('test.d'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    percentage = db.Column(db.Numeric(5,2)
    
    def to_json(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'test_id': self.test_id,
            'topic_id': self.topic_id,
            'percentage': float(self.percentage)
        }