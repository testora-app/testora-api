from app.extensions import db
from app._shared.models import BaseModel


class StudentTopicScores(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    score_acquired = db.Column(db.Numeric(5,2))
    
    def to_json(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'test_id': self.test_id,
            'topic_id': self.topic_id,
            'score_acquired': float(self.score_acquired)
        }
    

class StudentSubjectRecommendation(BaseModel):
    __tablename__ = 'student_subject_recommendation'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    recommendation_level = db.Column(db.String(50), nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    
    def to_json(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'topic_id': self.topic_id,
            'recommendation_level': self.recommendation_level,
            'is_archived': self.is_archived
        }


class StudentBestSubject(BaseModel):
    __tablename__ = 'student_best_subject'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    proficiency_level = db.Column(db.String(50), nullable=False)  # Assume proficiency_level is calculated elsewhere
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    
    def to_json(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'topic_id': self.topic_id,
            'proficiency_level': self.proficiency_level,
            'is_archived': self.is_archived
        }