import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.achievements.models import StudentHasAchievement, Achievement
from app.extensions import db
from app.integrations.pusher import pusher
from app.student.models import Student, StudentSubjectLevel
from app.test.models import Test

class AchievementEngine:
    def __init__(self, student_id):
        self.student_id = student_id

    BELOW_AP_THRESHOLD = 65  # below "approaching_proficient" in AnalyticsService

    # ---------- Persistence helpers ----------

    def assign(self, name: str, repeatable: bool = False) -> None:
        """Assign an achievement by its unique name."""
        achievement = Achievement.query.filter_by(name=name).first()
        if not achievement:
            return

        exists = StudentHasAchievement.query.filter_by(
            student_id=self.student_id,
            achievement_id=achievement.id,
        ).first()

        if exists:
            if repeatable:
                exists.number_of_times = (exists.number_of_times or 1) + 1
                exists.updated_at = datetime.now(timezone.utc)
                db.session.commit()
            return

        try:
            new_achievement = StudentHasAchievement(
                student_id=self.student_id,
                achievement_id=achievement.id,
                number_of_times=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(new_achievement)
            db.session.commit()
        except Exception as e:
            print(f"Error assigning achievement {name}: {e}")
            db.session.rollback()

    def _parse_requirements(self, achievement: Achievement) -> Dict[str, Any]:
        if not achievement.requirements:
            return {}
        try:
            return json.loads(achievement.requirements)
        except Exception:
            return {}

    # ---------- Metrics ----------

    def _tests_completed_total(self) -> int:
        from app.test.operations import test_manager
        return len(test_manager.get_tests_by_student_ids([self.student_id]))

    def _tests_scored_within_band_total(self, score_min: float, score_max: float) -> int:
        from app.test.operations import test_manager
        tests = test_manager.get_tests_by_student_ids([self.student_id])
        return sum(1 for t in tests if score_min <= float(t.score_acquired) <= score_max)

    def _has_previous_failure_below_ap(self, exclude_test_id: Optional[int] = None) -> bool:
        """Any prior test with score < BELOW_AP_THRESHOLD."""
        from app.test.operations import test_manager
        tests = test_manager.get_tests_by_student_ids([self.student_id])
        for t in tests:
            if exclude_test_id is not None and t.id == exclude_test_id:
                continue
            if float(t.score_acquired) < self.BELOW_AP_THRESHOLD:
                return True
        return False

    def _student_current_streak(self) -> int:
        student = Student.query.get(self.student_id)
        return int(student.current_streak or 0) if student else 0

    def _student_max_level(self) -> int:
        levels = StudentSubjectLevel.query.filter_by(student_id=self.student_id).all()
        return max((lvl.level for lvl in levels), default=0)

    # ---------- Evaluation ----------

    def evaluate_for_test(self, test: Test, email: Optional[str] = None) -> List[str]:
        """Evaluate and assign achievements triggered by a completed test."""
        unlocked: List[str] = []
        all_achievements = Achievement.query.filter_by(is_deleted=False).all()

        test_score = float(test.score_acquired)
        meta = test.meta or {}
        total_questions = meta.get("total_questions") or test.question_number
        mistakes_count = meta.get("mistakes_count")
        out_time = (meta.get("out_time") or 0) if isinstance(meta, dict) else 0

        for ach in all_achievements:
            req = self._parse_requirements(ach)
            aclass = ach.achievement_class

            # Volume practice
            if aclass == "volume_practice":
                target = int(req.get("number_of_tests") or 0)
                if target and self._tests_completed_total() >= target:
                    self.assign(ach.name)
                    unlocked.append(ach.name)
                continue

            # Comeback rewards
            if aclass == "comeback_rewards":
                cur_min = float(req.get("current_score_min") or 0)
                cur_max = float(req.get("current_score_max") or 0)
                requires_prev_fail = bool(req.get("requires_previous_failure"))
                prev_cond = req.get("previous_failure_condition")

                if not (cur_min <= test_score <= cur_max):
                    continue

                if requires_prev_fail:
                    if prev_cond == "below_AP":
                        if not self._has_previous_failure_below_ap(exclude_test_id=test.id):
                            continue
                    else:
                        continue

                self.assign(ach.name)
                unlocked.append(ach.name)
                continue

            # Speed and accuracy
            if aclass == "speed_and_accuracy":
                expected_q = req.get("questions_count")
                if expected_q is not None and total_questions is not None:
                    if int(total_questions) != int(expected_q):
                        continue

                if req.get("requires_finish_before_time_end"):
                    # Frontend sends out_time; if it's > 0, student finished before timer ended.
                    if not (out_time and int(out_time) > 0):
                        continue

                # Mistakes-based
                if req.get("metric") == "mistakes_count":
                    max_mistakes = req.get("max_mistakes")
                    if mistakes_count is None:
                        continue
                    if max_mistakes is not None and int(mistakes_count) > int(max_mistakes):
                        continue
                    self.assign(ach.name)
                    unlocked.append(ach.name)
                    continue

                # Score-based
                if req.get("metric") == "score_percent":
                    score_min = float(req.get("score_min") or 0)
                    score_max = float(req.get("score_max") or 100)
                    if score_min <= test_score <= score_max:
                        self.assign(ach.name)
                        unlocked.append(ach.name)
                    continue

                continue

            # Mastery level (score bands)
            if aclass == "mastery_level":
                score_min = float(req.get("score_band_min") or 0)
                score_max = float(req.get("score_band_max") or 0)
                required_tests = int(req.get("number_of_tests") or 0)
                if required_tests <= 0:
                    continue

                current = self._tests_scored_within_band_total(score_min, score_max)
                if current >= required_tests:
                    self.assign(ach.name)
                    unlocked.append(ach.name)
                continue

            # Level ups (checked here too, on every test completion)
            if aclass == "level_ups":
                target_level = int(req.get("level") or 0)
                if target_level and self._student_max_level() >= target_level:
                    self.assign(ach.name)
                    unlocked.append(ach.name)
                continue

            # Continuous practice (streak)
            if aclass == "continuous_practice":
                streak_days = int(req.get("streak_days") or 0)
                if streak_days and self._student_current_streak() >= streak_days:
                    self.assign(ach.name)
                    unlocked.append(ach.name)
                continue

        # Notify only newly unlocked items (best-effort).
        if email:
            for name in unlocked:
                AchievementEngine.notify_achievements(email, name)

        return unlocked

    # Backward-compat wrappers (kept so call sites don't break)
    def check_test_achievements(self, subject_id, score, test_count, email=None):
        test = (
            Test.query.filter_by(student_id=self.student_id, is_completed=True)
            .order_by(Test.finished_on.desc())
            .first()
        )
        if test:
            self.evaluate_for_test(test, email=email)

    def check_level_achievements(self, email=None):
        # level achievements are evaluated inside evaluate_for_test()
        return

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
