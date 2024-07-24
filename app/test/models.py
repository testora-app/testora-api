from app.extensions import db
from app._shared.models import BaseModel
from datetime import datetime
import ast


class Question(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    possible_answers = db.Column(db.Text, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    points = db.Column(db.Integer, nullable=True, default=None)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True)
    
    sub_questions = db.relationship('SubQuestion', backref='parent_question', lazy=True)
    topic = db.relationship('Topic', back_populates='questions')

    def to_json(self, include_correct_answer=True):
        question_json = {
            'id': self.id,
            'text': self.text,
            'possible_answers': ast.literal_eval(self.possible_answers),
            'topic_id': self.topic_id,
            'points': self.points,
            'school_id': self.school_id,
            'sub_questions': [sub_question.to_json(include_correct_answer=include_correct_answer) for sub_question in self.sub_questions],
            'level': self.topic.level
        }

        if include_correct_answer:
            question_json['correct_answer'] = self.correct_answer
        return question_json


class SubQuestion(BaseModel):
    __tablename__ = 'sub_question'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    possible_answers = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False)

    def to_json(self, include_correct_answer=True):
        question_json = {
            'id': self.id,
            'parent_question_id': self.parent_question_id,
            'text': self.text,
            'possible_answers': ast.literal_eval(self.possible_answers),
            'points': self.points
        }

        if include_correct_answer:
            question_json['correct_answer'] = self.correct_answer
        return question_json
    

class Test(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    questions = db.Column(db.JSON, nullable=False)
    total_points = db.Column(db.Integer, nullable=False)
    points_acquired = db.Column(db.Integer, nullable=False)
    total_score = db.Column(db.Numeric(5,2), nullable=False)
    score_acquired = db.Column(db.Numeric(5,2), nullable=False)
    started_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_on = db.Column(db.DateTime, nullable=True)
    question_number = db.Column(db.Integer, nullable=True)
    questions_correct = db.Column(db.Integer, nullable=True)
    meta = db.Column(db.JSON, nullable=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_json(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'questions': self.questions,
            'total_points': self.total_points,
            'points_acquired': self.points_acquired,
            'total_score': float(self.total_score),  # Convert Decimal to float
            'score_acquired': float(self.score_acquired),  # Convert Decimal to float
            'started_on': self.started_on,
            'finished_on': self.finished_on if self.finished_on else None,
            'question_number': self.question_number,
            'questions_correct': self.questions_correct,
            'meta': self.meta,
            'is_completed': self.is_completed,
            'school_id': self.school_id,
            'created_at': self.created_at
        }