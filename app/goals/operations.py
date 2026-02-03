from datetime import date, timedelta
from typing import List, Dict, Optional
import random
from sqlalchemy import func

from app.extensions import db
from app.test.operations import test_manager
from app.student.operations import stusublvl_manager
from app.app_admin.operations import subject_manager
from app.goals.models import WeeklyGoal, GoalStatus, GoalMetric
from app.analytics.weekly_messages_generator import GoalMessageGenerator


def calculate_subject_averages(student_id: int) -> List[Dict]:
    """
    Calculate average scores for each subject based on last 5 tests.
    
    Args:
        student_id: The student's ID
        
    Returns:
        List of dicts with keys: 'subject_id', 'avg_score', 'level'
        If no tests exist, returns subjects with avg_score=0
    """
    from app.student.operations import student_manager
    
    student = student_manager.get_student_by_id(student_id)
    if not student:
        return []
    
    # Get all unique subjects from student's batches
    subject_ids = set()
    for batch in student.batches:
        batch_subjects = subject_manager.get_subject_by_curriculum(batch.curriculum)
        for subject in batch_subjects:
            subject_ids.add(subject.id)
    
    if not subject_ids:
        return []
    
    result = []
    
    for subject_id in subject_ids:
        # Get student's level for this subject
        student_level = stusublvl_manager.get_student_subject_level(student_id, subject_id)
        
        # Initialize level if not exists
        if not student_level:
            student_level = stusublvl_manager.init_student_subject_level(student_id, subject_id)
        
        # Get last 5 tests for this subject
        recent_tests = test_manager.get_student_recent_tests(
            student_id, 
            subject_id=subject_id, 
            limit=5
        )
        
        # Calculate average score
        if recent_tests and len(recent_tests) > 0:
            avg_score = sum(test.score_acquired for test in recent_tests) / len(recent_tests)
        else:
            avg_score = 0.0
        
        result.append({
            'subject_id': subject_id,
            'avg_score': round(avg_score, 2),
            'level': student_level.level
        })
    
    # If no tests at all (all subjects have avg_score=0), select random 3 subjects
    if all(subj['avg_score'] == 0 for subj in result):
        # Return all subjects but mark for random selection
        for subj in result:
            subj['_needs_random_selection'] = True
    
    return result


def calculate_max_streak_30d(student_id: int, current_date: date) -> int:
    """
    Calculate maximum consecutive days streak in the last 30 days.
    
    Args:
        student_id: The student's ID
        current_date: The current date (in Africa/Accra timezone)
        
    Returns:
        Maximum streak count in last 30 days
    """
    # Calculate the date 30 days ago
    start_date = current_date - timedelta(days=30)
    
    # Get all completed tests in the last 30 days
    tests = test_manager.get_tests_by_student_ids([student_id])
    
    # Filter tests to only those completed in last 30 days
    completed_dates = set()
    for test in tests:
        if test.finished_on:
            test_date = test.finished_on.date()
            if start_date <= test_date <= current_date:
                completed_dates.add(test_date)
    
    if not completed_dates:
        return 0
    
    # Sort dates
    sorted_dates = sorted(completed_dates)
    
    # Calculate max consecutive streak
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(sorted_dates)):
        # Check if dates are consecutive
        if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    
    return max_streak


def select_subjects_for_goals(subjects: List[Dict]) -> List[Dict]:
    """
    Select subjects for goal generation.
    Handles the special case where all subjects have avg_score=0.
    
    Args:
        subjects: List of subject dicts with 'subject_id', 'avg_score', 'level'
        
    Returns:
        Selected subjects with 'role' field added
    """
    if not subjects:
        return []
    
    # Check if we need random selection (all avg_scores are 0)
    needs_random = all(subj.get('_needs_random_selection', False) for subj in subjects)
    
    if needs_random:
        # Remove the flag
        for subj in subjects:
            subj.pop('_needs_random_selection', None)
        
        # Randomly select 3 subjects
        num_to_select = min(3, len(subjects))
        selected = random.sample(subjects, num_to_select)
        
        # All selected subjects are treated as 'lowest' for goal calculation
        for subj in selected:
            subj['role'] = 'lowest'
        
        return selected
    
    # Normal case: use avg_score to select
    # Sort by avg_score ascending, then by subject_id for tie-breaking
    sorted_subjects = sorted(subjects, key=lambda s: (s['avg_score'], s['subject_id']))
    
    # Get lowest 3
    lowest_3 = sorted_subjects[:3]
    for subj in lowest_3:
        subj['role'] = 'lowest'
    
    selected = lowest_3.copy()
    
    # Get highest 1 if we have at least 4 subjects
    if len(subjects) >= 4:
        highest_1 = sorted_subjects[-1]
        # Make sure it's not already in lowest_3
        if highest_1['subject_id'] not in [s['subject_id'] for s in lowest_3]:
            highest_1['role'] = 'highest'
            selected.append(highest_1)
    
    return selected


def get_weekly_wins_message(student_id: int, week_start_date: date, week_offset: int = 0) -> Dict:
    """
    Generate weekly wins celebration message for achieved goals in a specified week.

    Args:
        student_id: The student's ID
        week_start_date: Start date of the reference week
        week_offset: Number of weeks to offset from week_start_date (e.g., -1 for previous week, 1 for next week)

    Returns:
        {
            "has_wins": bool,
            "message": str,  # Formatted celebration message
            "achievements": [...]  # Individual achievement details
        }
    """
    # Calculate target week start date based on offset
    target_week_start = week_start_date + timedelta(days=7 * week_offset)

    # Query achieved goals for the target week
    achieved_goals = db.session.query(WeeklyGoal).filter(
        WeeklyGoal.student_id == student_id,
        WeeklyGoal.week_start_date == target_week_start,
        WeeklyGoal.status == GoalStatus.achieved
    ).all()
    
    if not achieved_goals:
        return {
            "has_wins": False,
            "message": "",
            "achievements": []
        }
    
    # Calculate week progress (0.0 to 1.0) - how far through the week are we
    current_date = date.today()
    days_elapsed = (current_date - week_start_date).days
    week_progress = min(days_elapsed / 7.0, 1.0)
    
    achievement_messages = []
    achievement_details = []
    
    for goal in achieved_goals:
        try:
            # Get subject name if applicable
            subject_name = None
            if goal.subject_id:
                subject = subject_manager.get_subject_by_id(goal.subject_id)
                subject_name = subject.short_name if subject else None
            
            # Generate appropriate message based on metric type
            if goal.target_metric == GoalMetric.xp:
                message = GoalMessageGenerator.achievement(
                    metric=GoalMetric.xp,
                    subject=subject_name,
                    target=goal.target_value,
                    progress=goal.current_value,
                    week_progress=week_progress
                )
                achievement_details.append({
                    "type": "xp",
                    "subject": subject_name,
                    "target": goal.target_value,
                    "achieved": goal.current_value,
                    "achieved_at": goal.achieved_at.isoformat() if goal.achieved_at else None
                })
            
            elif goal.target_metric == GoalMetric.streak_days:
                message = GoalMessageGenerator.achievement(
                    metric=GoalMetric.streak_days,
                    value=goal.current_value,
                    target=goal.target_value,
                    week_progress=week_progress
                )
                achievement_details.append({
                    "type": "streak",
                    "days": goal.current_value,
                    "target": goal.target_value,
                    "achieved_at": goal.achieved_at.isoformat() if goal.achieved_at else None
                })
            
            achievement_messages.append(message)
            
        except Exception as e:
            # Log but don't fail if one goal's message generation fails
            from logging import error as log_error
            log_error(f"Error generating message for goal {goal.id}: {str(e)}")
            continue
    
    if not achievement_messages:
        return {
            "has_wins": False,
            "message": "",
            "achievements": []
        }
    
    # Format as weekly summary
    summary_message = GoalMessageGenerator.weekly_summary(achievement_messages)
    
    return {
        "has_wins": True,
        "message": summary_message,
        "achievements": achievement_details
    }
