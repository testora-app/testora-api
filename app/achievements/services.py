from app.achievements.models import StudentHasAchievement, Achievement
from app.student.models import StudentSubjectLevel
from app.extensions import db
from datetime import datetime, timezone

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
                db.session.commit()
                return
            return

        new_achievement = StudentHasAchievement(
            student_id=self.student_id,
            achievement_id=achievement.id,
            number_of_times=1,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(new_achievement)
        db.session.commit()

    def check_test_achievements(self, subject_id, score, test_count):
        if test_count == 1:
            self.assign("First Step")
        elif test_count == 5:
            self.assign("Steady Start")
        elif test_count == 10:
            self.assign("Practice Champ")
        elif test_count == 25:
            self.assign("Quarter Milestone")

        if score == 100:
            self.assign("Top Scorer", repeatable=True)
        if score >= 90:
            self.assign("Precision Player", repeatable=True)
        if score >= 80:
            self.assign("80 Club", repeatable=True)
        if score >= 50 and test_count >= 5:
            self.assign("Rising Star")

    def check_level_achievements(self):
        levels = StudentSubjectLevel.query.filter_by(student_id=self.student_id).all()
        subjects_over_level3 = [lvl for lvl in levels if lvl.level >= 3]
        subject_ids = [lvl.subject_id for lvl in subjects_over_level3]

        if len(subject_ids) >= 3:
            self.assign("Multi-Subject Pro")

        for level in levels:
            subject_name = self.get_subject_name(level.subject_id)
            if subject_name == "Math" and level.level >= 5:
                self.assign("Math Level Up")

    @staticmethod
    def get_subject_name(subject_id):
        from app.app_admin.models import Subject
        subj = Subject.query.get(subject_id)
        return subj.name if subj else None
