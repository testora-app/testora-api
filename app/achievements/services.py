from app.achievements.models import StudentHasAchievement, Achievement
from app.student.models import StudentSubjectLevel
from app.extensions import db
from datetime import datetime, timezone
from app.integrations.pusher import pusher

class AchievementEngine:
    def __init__(self, student_id):
        self.student_id = student_id

    def assign(self, name, repeatable=False):
        achievement = Achievement.query.filter_by(name=name).first()
        if not achievement:
            return

        exists = StudentHasAchievement.query.filter_by(
            student_id=self.student_id,
            achievement_id=achievement.id
        ).first()

        if exists:
            if repeatable:
                exists.number_of_times += 1
                exists.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                return
            return
        
        try:
            new_achievement = StudentHasAchievement(
                student_id=self.student_id,
                achievement_id=achievement.id,
                number_of_times=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        
            db.session.add(new_achievement)
            db.session.commit()
        except Exception as e:
            print(f"Error assigning achievement {name}: {e}")
            db.session.rollback()

    def check_test_achievements(self, subject_id, score, test_count, email=None):
        if test_count == 1:
            self.assign("First Step")
            AchievementEngine.notify_achievements(email, "First Step")
        elif test_count == 5:
            self.assign("Steady Start")
            AchievementEngine.notify_achievements(email, "Steady Start")
        elif test_count == 10:
            self.assign("Practice Champ")
            AchievementEngine.notify_achievements(email, "Practice Champ")
        elif test_count == 25:
            self.assign("Quarter Milestone")
            AchievementEngine.notify_achievements(email, "Quarter Milestone")

        if score == 100:
            self.assign("Top Scorer", repeatable=True)
            AchievementEngine.notify_achievements(email, "Top Scorer")
        if score >= 90:
            self.assign("Precision Player", repeatable=True)
            AchievementEngine.notify_achievements(email, "Precision Player")
        if score >= 80:
            self.assign("80 Club", repeatable=True)
            AchievementEngine.notify_achievements(email, "80 Club")
        if score >= 50 and test_count >= 5:
            self.assign("Rising Star")
            AchievementEngine.notify_achievements(email, "Rising Star")

    def check_level_achievements(self, email=None):
        levels = StudentSubjectLevel.query.filter_by(student_id=self.student_id).all()
        subjects_over_level3 = [lvl for lvl in levels if lvl.level >= 3]
        subject_ids = [lvl.subject_id for lvl in subjects_over_level3]

        if len(subject_ids) >= 3:
            self.assign("Multi-Subject Pro")
            AchievementEngine.notify_achievements(email, "Multi-Subject Pro")

        for level in levels:
            subject_name = self.get_subject_name(level.subject_id)
            if subject_name == "Math" and level.level >= 5:
                self.assign("Math Level Up")
                AchievementEngine.notify_achievements(email, "Math Level Up")

    
    @staticmethod
    def notify_achievements(email, achievement_name):
        if not email:
            return
        pusher.notify_devices(
            title="New Achievement Unlocked!",
            content=f"You have unlocked a new achievement: {achievement_name}",
            emails=[email],
        )

    @staticmethod
    def get_subject_name(subject_id):
        from app.app_admin.models import Subject
        subj = Subject.query.get(subject_id)
        return subj.name if subj else None
