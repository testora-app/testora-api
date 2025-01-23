from app.extensions import db
from app._shared.models import BaseModel


class Achievement(BaseModel):
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    image_url = db.Column(db.String(100), nullable=False)
    requirements = db.Column(db.Text, nullable=True)

    def to_json(self, include_requirements=False):
        obj = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url
        }
        if include_requirements:
            obj["requirements"] = self.requirements
        return obj


class StudentHasAchievement(BaseModel):
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    achievement_id = db.Column(
        db.Integer, db.ForeignKey("achievement.id"), nullable=False
    )
    number_of_times = db.Column(db.Integer, nullable=True, default=1)


    def to_json(self):
        return {"student_id": self.student_id, "achievement_id": self.achievement_id, "number_of_times": self.number_of_times}
