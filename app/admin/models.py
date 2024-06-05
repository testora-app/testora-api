from datetime import datetime

from app.extensions import db
from app._shared.models import BaseModel


class Admin(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_super_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return f'{self.username}'
    
    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_super_admin': self.is_super_admin,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    

class Subject(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    short_name = db.Column(db.String(20), nullable=False, unique=True)
    curriculum = db.Column(db.String(20), nullable=False) # bece, igsce

    def __str__(self):
        return f'{self.name}, Curriculum: {self.curriculum}'
    
    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'curriculum': self.curriculum
        }
    

class Topic(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    short_name = db.Column(db.String(20), nullable=False, unique=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)

    sub_topics = db.relationship('SubTopic', backref='topic', lazy=True)

    def __str__(self):
        return f'{self.name} -- {self.subject_id}, Level: {self.level}'
    
    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'subject_id': self.subject_id,
            'level': self.level,
            'sub_topics': [sub_topic.to_json() for sub_topic in self.sub_topics]
        }


class SubTopic(BaseModel):
    __tablename__ = 'sub_topic'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    short_name = db.Column(db.String(20), nullable=False, unique=True)
    level = db.Column(db.Integer, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)


    def __str__(self):
        return f'{self.name} -- {self.topic_id}'
    
    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'level': self.level,
            'topic_id': self.topic_id
        }