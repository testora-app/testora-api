from datetime import date, timedelta
from typing import Optional
from sqlalchemy import and_, or_
from app.extensions import db
from app.goals.models import WeeklyGoal, GoalStatus, GoalMetric


def find_active_week_start(student_id: int, login_date: date) -> Optional[date]:
    """
    Returns the week_start_date of an existing active window that includes login_date,
    else None. Active window = [week_start_date .. week_start_date + 6].
    """
    # Query for any goal where:
    # week_start_date <= login_date AND week_start_date + 6 >= login_date
    goal = db.session.query(WeeklyGoal.week_start_date).filter(
        WeeklyGoal.student_id == student_id,
        WeeklyGoal.week_start_date <= login_date,
        WeeklyGoal.week_start_date + timedelta(days=6) >= login_date
    ).first()
    
    return goal[0] if goal else None


def expire_old_windows(student_id: int, cutoff: date) -> int:
    """
    Set status='expired' for goals whose (week_start_date + 6) < cutoff
    and status is not 'achieved' or 'expired'.
    Returns the count of expired goals.
    """
    expired_count = db.session.query(WeeklyGoal).filter(
        WeeklyGoal.student_id == student_id,
        WeeklyGoal.week_start_date + timedelta(days=6) < cutoff,
        WeeklyGoal.status.notin_([GoalStatus.achieved, GoalStatus.expired])
    ).update(
        {WeeklyGoal.status: GoalStatus.expired},
        synchronize_session='fetch'
    )
    
    db.session.commit()
    return expired_count


class GenerateGoalsService:
    """
    Service to generate weekly goals for a student based on login date.
    
    RULE: A "week" starts on the first login when the student has no active weekly goals;
    week_start_date = login_date (Africa/Accra timezone).
    
    If the student already has any weekly_goals whose window includes login_date,
    skip generation entirely — do not create or modify goals.
    """
    
    def run(
        self,
        student_id: int,
        login_date: date,
        subjects: list[dict],
        student_max_streak_30d: int
    ) -> dict:
        """
        Generate weekly goals for a student.
        
        Args:
            student_id: The student's ID
            login_date: The date of login (Africa/Accra timezone)
            subjects: List of subject dicts with keys: 'subject_id', 'avg_score', 'level'
            student_max_streak_30d: Student's maximum streak in last 30 days
            
        Returns:
            dict with either:
            - {"skipped": true, "reason": "active_goals_exist", "week_start_date": "YYYY-MM-DD"}
            - {"created": [...], "summary": {...}}
        """
        # Check if there's an active window covering login_date
        active_week = find_active_week_start(student_id, login_date)
        if active_week:
            return {
                "skipped": True,
                "reason": "active_goals_exist",
                "week_start_date": str(active_week)
            }
        
        # Expire old windows
        expired_count = expire_old_windows(student_id, login_date)
        
        # Set week start to login date (new window)
        week_start = login_date
        
        # Select subjects for goals
        selected_subjects = self._select_subjects(subjects)
        
        # Generate goals
        created_goals = []
        
        # Create XP goals for selected subjects
        for subj in selected_subjects:
            xp_target = self._calculate_xp_target(subj['level'], subj['role'])
            
            goal = WeeklyGoal(
                student_id=student_id,
                subject_id=subj['subject_id'],
                week_start_date=week_start,
                status=GoalStatus.pending,
                target_metric=GoalMetric.xp,
                target_value=xp_target,
                current_value=0,
                params={"role": subj['role'], "level": subj['level']}
            )
            db.session.add(goal)
            created_goals.append({
                "subject_id": subj['subject_id'],
                "metric": "xp",
                "target": xp_target,
                "role": subj['role']
            })
        
        # Create streak goal (subject-agnostic)
        streak_target = self._calculate_streak_target(student_max_streak_30d)
        
        streak_goal = WeeklyGoal(
            student_id=student_id,
            subject_id=None,  # NULL for subject-agnostic
            week_start_date=week_start,
            status=GoalStatus.pending,
            target_metric=GoalMetric.streak_days,
            target_value=streak_target,
            current_value=0,
            params={"streak_scope": "subject_agnostic"}
        )
        db.session.add(streak_goal)
        created_goals.append({
            "subject_id": None,
            "metric": "streak_days",
            "target": streak_target,
            "scope": "subject_agnostic"
        })
        
        # Commit all goals
        db.session.commit()
        
        return {
            "created": created_goals,
            "summary": {
                "week_start_date": str(week_start),
                "week_end_date": str(week_start + timedelta(days=6)),
                "xp_goals_count": len(selected_subjects),
                "streak_goals_count": 1,
                "total_goals": len(created_goals),
                "expired_old_goals": expired_count
            }
        }
    
    def _select_subjects(self, subjects: list[dict]) -> list[dict]:
        """
        Select subjects for goal generation:
        - 3 lowest avg subjects (tie → lower subject_id)
        - 1 highest avg subject
        
        Returns list of dicts with 'subject_id', 'avg_score', 'level', and 'role' (lowest/highest)
        """
        if not subjects:
            return []
        
        # Sort by avg_score ascending, then by subject_id ascending for tie-breaking
        sorted_subjects = sorted(subjects, key=lambda s: (s['avg_score'], s['subject_id']))
        
        # Get lowest 3
        lowest_3 = sorted_subjects[:3]
        for subj in lowest_3:
            subj['role'] = 'lowest'
        
        # Get highest 1 (if we have at least 4 subjects, otherwise highest might overlap with lowest)
        selected = lowest_3.copy()
        
        if len(subjects) >= 4:
            # Get the highest (last in sorted list)
            highest_1 = sorted_subjects[-1]
            # Make sure it's not already in lowest_3
            if highest_1['subject_id'] not in [s['subject_id'] for s in lowest_3]:
                highest_1['role'] = 'highest'
                selected.append(highest_1)
        elif len(subjects) == 3:
            # All 3 are already selected as lowest, no separate highest
            pass
        elif len(subjects) == 2:
            # We have 2 subjects: both are in lowest
            pass
        elif len(subjects) == 1:
            # Only 1 subject: it's both lowest and highest, but we only add it once
            pass
        
        return selected
    
    def _calculate_xp_target(self, level: int, role: str) -> int:
        """
        Calculate XP target based on level and role.
        
        Level bands:
        - L1-3: 200-300
        - L4-6: 300-450
        - L7-9: 400-600
        
        Lowest 3 → upper half of band
        Highest → mid of band
        """
        if level <= 3:
            # Band: 200-300
            if role == 'lowest':
                # Upper half: 250-300, use 275
                return 275
            else:  # highest
                # Mid of band: 250
                return 250
        elif level <= 6:
            # Band: 300-450
            if role == 'lowest':
                # Upper half: 375-450, use 412
                return 412
            else:  # highest
                # Mid of band: 375
                return 375
        else:  # level 7-9
            # Band: 400-600
            if role == 'lowest':
                # Upper half: 500-600, use 550
                return 550
            else:  # highest
                # Mid of band: 500
                return 500
    
    def _calculate_streak_target(self, student_max_streak_30d: int) -> int:
        """
        Calculate streak target from student_max_streak_30d.
        
        Rules:
        - Minimum: 3
        - If student_max_streak_30d >= 5: target = 5
        - If student_max_streak_30d >= 4: target = 4
        - Otherwise: target = 3
        """
        if student_max_streak_30d >= 5:
            return 5
        elif student_max_streak_30d >= 4:
            return 4
        else:
            return 3
