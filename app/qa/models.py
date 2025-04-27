"""
Model for storing student Q&A interactions with ChatGPT
"""
from datetime import datetime
from app.extensions import db


class StudentQuestion(db.Model):
    """
    Model to store questions asked by students and the answers provided by ChatGPT
    """
    __tablename__ = 'student_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<StudentQuestion {self.id}: {self.question[:30]}...>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "school_id": self.school_id,
            "subject": self.subject,
            "topic": self.topic,
            "question": self.question,
            "answer": self.answer,
            "created_at": self.created_at.isoformat()
        }
    
    def save(self):
        """Save the current instance to the database"""
        db.session.add(self)
        db.session.commit()