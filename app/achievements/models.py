from app.extensions import db
from app._shared.models import BaseModel

class Achievement(BaseModel):
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    image_url = db.Column(db.String(100), nullable=False)
    requirements = db.Column(db.Text, nullable=True)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'requirements': self.requirements
        }
    

class StudentHasAchievement(BaseModel):
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)

    def to_json(self):
        return {
            'student_id': self.student_id,
            'achievement_id': self.achievement_id
        }