from app._shared.operations import BaseManager
from .models import Achievement, StudentHasAchievement

from typing import List


class AchievementManager(BaseManager):
    def get_achievements(self) -> List[Achievement]:
        return Achievement.query.all()
    
    def get_achievement(self, achievement_id) -> Achievement:
        return Achievement.query.filter_by(id=achievement_id).first()

    def add_achievement(
        self, name, description, image_url, requirements=None
    ) -> Achievement:
        return Achievement(
            name=name,
            description=description,
            image_url=image_url,
            requirements=requirements,
        )


class StudentHasAchievementManager(BaseManager):
    def add_student_achievement(
        self, student_id, achievement_id
    ) -> StudentHasAchievement:
        return StudentHasAchievement(
            student_id=student_id, achievement_id=achievement_id
        )

    def get_student_achievements(self, student_id) -> List[StudentHasAchievement]:
        return StudentHasAchievement.query.filter_by(student_id=student_id).all()
    
    def get_student_achievements_number(self, student_id) -> int:
        return StudentHasAchievement.query.filter_by(student_id=student_id).count()

    def get_student_achievement(
        self, student_id, achievement_id
    ) -> StudentHasAchievement:
        return StudentHasAchievement.query.filter_by(
            student_id=student_id, achievement_id=achievement_id
        ).first()

    def delete_student_achievement(
        self, student_id, achievement_id
    ) -> StudentHasAchievement:
        return StudentHasAchievement.query.filter_by(
            student_id=student_id, achievement_id=achievement_id
        ).delete()


achievement_manager = AchievementManager()
student_has_achievement_manager = StudentHasAchievementManager()
