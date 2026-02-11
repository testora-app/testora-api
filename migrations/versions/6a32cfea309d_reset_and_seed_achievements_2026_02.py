"""reset_and_seed_achievements_2026_02

Revision ID: 6a32cfea309d
Revises: 98b900b10c10
Create Date: 2026-02-11 11:27:59.500493

"""
from alembic import op
import sqlalchemy as sa

import json
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = '6a32cfea309d'
down_revision = '98b900b10c10'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Clear dependent table first
    op.execute(sa.text("DELETE FROM student_has_achievement"))

    # 2) Clear achievements table
    op.execute(sa.text("DELETE FROM achievement"))

    achievement_table = sa.table(
        "achievement",
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("image_url", sa.String),
        sa.column("requirements", sa.Text),
        sa.column("achievement_class", sa.String),
        sa.column("is_deleted", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    # Source of truth: c:/Users/jjnra/Downloads/rewards.json
    # We embed the payload here so the migration is self-contained.
    achievements = [
        {
            "name": "First Test Taken!",
            "description": "Completed the first test in any subject.",
            "achievement_class": "volume_practice",
            "metadata": {
                "number_of_tests": 1,
                "scope": "all_subjects",
                "metric": "tests_completed_total",
                "threshold_type": "at_least",
            },
        },
        {
            "name": "Practice Champ I",
            "description": "Completed 10 tests across all subjects.",
            "achievement_class": "volume_practice",
            "metadata": {
                "number_of_tests": 10,
                "scope": "all_subjects",
                "metric": "tests_completed_total",
                "threshold_type": "at_least",
            },
        },
        {
            "name": "Practice Champ II",
            "description": "Completed 25 tests across all subjects.",
            "achievement_class": "volume_practice",
            "metadata": {
                "number_of_tests": 25,
                "scope": "all_subjects",
                "metric": "tests_completed_total",
                "threshold_type": "at_least",
            },
        },
        {
            "name": "Practice Champ III",
            "description": "Completed 50 tests across all subjects.",
            "achievement_class": "volume_practice",
            "metadata": {
                "number_of_tests": 50,
                "scope": "all_subjects",
                "metric": "tests_completed_total",
                "threshold_type": "at_least",
            },
        },
        {
            "name": "Test Pilot",
            "description": "Completed 100 tests across all subjects.",
            "achievement_class": "volume_practice",
            "metadata": {
                "number_of_tests": 100,
                "scope": "all_subjects",
                "metric": "tests_completed_total",
                "threshold_type": "at_least",
            },
        },
        {
            "name": "Grand Tester",
            "description": "Completed 200 tests across all subjects.",
            "achievement_class": "volume_practice",
            "metadata": {
                "number_of_tests": 200,
                "scope": "all_subjects",
                "metric": "tests_completed_total",
                "threshold_type": "at_least",
            },
        },
        {
            "name": "Ultimate Tester",
            "description": "Completed 300+ tests across all subjects.",
            "achievement_class": "volume_practice",
            "metadata": {
                "number_of_tests": 300,
                "scope": "all_subjects",
                "metric": "tests_completed_total",
                "threshold_type": "at_least",
                "plus": True,
            },
        },
        {
            "name": "Bounce Back",
            "description": "Takes a new test and scores 80–89% after a previously failed result (below AP).",
            "achievement_class": "comeback_rewards",
            "metadata": {
                "current_score_min": 80,
                "current_score_max": 89,
                "requires_previous_failure": True,
                "previous_failure_condition": "below_AP",
                "scope": "all_subjects",
                "event": "test_completed",
            },
        },
        {
            "name": "Bounce Back Pro",
            "description": "Takes a new test and scores 90–99% after a previously failed result (below AP).",
            "achievement_class": "comeback_rewards",
            "metadata": {
                "current_score_min": 90,
                "current_score_max": 99,
                "requires_previous_failure": True,
                "previous_failure_condition": "below_AP",
                "scope": "all_subjects",
                "event": "test_completed",
            },
        },
        {
            "name": "Legendary Bounce Back",
            "description": "Takes a new test and scores 100% after a previously failed result (below AP).",
            "achievement_class": "comeback_rewards",
            "metadata": {
                "current_score_min": 100,
                "current_score_max": 100,
                "requires_previous_failure": True,
                "previous_failure_condition": "below_AP",
                "scope": "all_subjects",
                "event": "test_completed",
            },
        },
        {
            "name": "Flawless 20 Accuracy",
            "description": "Fewer than 2 mistakes on a 20-question test completed before time ends.",
            "achievement_class": "speed_and_accuracy",
            "metadata": {
                "questions_count": 20,
                "max_mistakes": 1,
                "timed": True,
                "requires_finish_before_time_end": True,
                "metric": "mistakes_count",
                "event": "test_completed",
            },
        },
        {
            "name": "Flawless 25 Accuracy",
            "description": "Fewer than 2 mistakes on a 25-question test completed before time ends.",
            "achievement_class": "speed_and_accuracy",
            "metadata": {
                "questions_count": 25,
                "max_mistakes": 1,
                "timed": True,
                "requires_finish_before_time_end": True,
                "metric": "mistakes_count",
                "event": "test_completed",
            },
        },
        {
            "name": "Flawless 30 Accuracy",
            "description": "Fewer than 2 mistakes on a 30-question test completed before time ends.",
            "achievement_class": "speed_and_accuracy",
            "metadata": {
                "questions_count": 30,
                "max_mistakes": 1,
                "timed": True,
                "requires_finish_before_time_end": True,
                "metric": "mistakes_count",
                "event": "test_completed",
            },
        },
        {
            "name": "Flawless 40 Accuracy",
            "description": "Fewer than 2 mistakes on a 40-question test completed before time ends.",
            "achievement_class": "speed_and_accuracy",
            "metadata": {
                "questions_count": 40,
                "max_mistakes": 1,
                "timed": True,
                "requires_finish_before_time_end": True,
                "metric": "mistakes_count",
                "event": "test_completed",
            },
        },
        {
            "name": "Perfect 20",
            "description": "Scored 100% on a 20-question test completed before time ends.",
            "achievement_class": "speed_and_accuracy",
            "metadata": {
                "questions_count": 20,
                "score_min": 100,
                "score_max": 100,
                "timed": True,
                "requires_finish_before_time_end": True,
                "metric": "score_percent",
                "event": "test_completed",
            },
        },
        {
            "name": "Absolute Ace",
            "description": "Scored 100% on a 25-question timed test before time ends.",
            "achievement_class": "speed_and_accuracy",
            "metadata": {
                "questions_count": 25,
                "score_min": 100,
                "score_max": 100,
                "timed": True,
                "requires_finish_before_time_end": True,
                "metric": "score_percent",
                "event": "test_completed",
            },
        },
        {
            "name": "Star Champ",
            "description": "Scored 100% on a 30-question timed test before time ends.",
            "achievement_class": "speed_and_accuracy",
            "metadata": {
                "questions_count": 30,
                "score_min": 100,
                "score_max": 100,
                "timed": True,
                "requires_finish_before_time_end": True,
                "metric": "score_percent",
                "event": "test_completed",
            },
        },
        {
            "name": "Zenith Precision",
            "description": "Scored 100% on a 40-question timed test before time ends.",
            "achievement_class": "speed_and_accuracy",
            "metadata": {
                "questions_count": 40,
                "score_min": 100,
                "score_max": 100,
                "timed": True,
                "requires_finish_before_time_end": True,
                "metric": "score_percent",
                "event": "test_completed",
            },
        },
        {
            "name": "Trail Starter",
            "description": "Welcome! You’ve just begun your learning journey.",
            "achievement_class": "level_ups",
            "metadata": {"level": 1, "event": "level_up"},
        },
        {
            "name": "Pathfinder",
            "description": "You’re finding your way! Reached Level 2.",
            "achievement_class": "level_ups",
            "metadata": {"level": 2, "event": "level_up"},
        },
        {
            "name": "Route Seeker",
            "description": "You’re building momentum! Levelled up to Level 3.",
            "achievement_class": "level_ups",
            "metadata": {"level": 3, "event": "level_up"},
        },
        {
            "name": "Builder Quest",
            "description": "You're pushing forward! Reached Level 4.",
            "achievement_class": "level_ups",
            "metadata": {"level": 4, "event": "level_up"},
        },
        {
            "name": "Knowledge Rider",
            "description": "Halfway there! Levelled up to Level 5.",
            "achievement_class": "level_ups",
            "metadata": {"level": 5, "event": "level_up"},
        },
        {
            "name": "Skill Voyager",
            "description": "You’re gaining serious speed! Reached Level 6.",
            "achievement_class": "level_ups",
            "metadata": {"level": 6, "event": "level_up"},
        },
        {
            "name": "Trail Captain",
            "description": "Your learning trail is deepening! Levelled up to Level 7.",
            "achievement_class": "level_ups",
            "metadata": {"level": 7, "event": "level_up"},
        },
        {
            "name": "Map Master",
            "description": "You’re charting the unknown! Reached Level 8.",
            "achievement_class": "level_ups",
            "metadata": {"level": 8, "event": "level_up"},
        },
        {
            "name": "Peak Climber",
            "description": "Almost at the summit! Levelled up to Level 9.",
            "achievement_class": "level_ups",
            "metadata": {"level": 9, "event": "level_up"},
        },
        {
            "name": "Summit Explorer",
            "description": "You’ve conquered all levels! Reached Level 10 — keep going!",
            "achievement_class": "level_ups",
            "metadata": {"level": 10, "event": "level_up"},
        },
        {
            "name": "Smooth Spark",
            "description": "Completed tests for 3 days in a row — you're getting started!",
            "achievement_class": "continuous_practice",
            "metadata": {
                "streak_days": 3,
                "metric": "daily_test_streak",
                "event": "streak_reached",
            },
        },
        {
            "name": "Rising Spark",
            "description": "A full week of daily test practice — strong momentum!",
            "achievement_class": "continuous_practice",
            "metadata": {
                "streak_days": 7,
                "metric": "daily_test_streak",
                "event": "streak_reached",
            },
        },
        {
            "name": "Heat Spark",
            "description": "Two straight weeks of showing up — building a powerful habit!",
            "achievement_class": "continuous_practice",
            "metadata": {
                "streak_days": 14,
                "metric": "daily_test_streak",
                "event": "streak_reached",
            },
        },
        {
            "name": "Focus Fire",
            "description": "You’ve practised for 3 full weeks — that’s discipline!",
            "achievement_class": "continuous_practice",
            "metadata": {
                "streak_days": 21,
                "metric": "daily_test_streak",
                "event": "streak_reached",
            },
        },
        {
            "name": "Steady Surge",
            "description": "A long and steady grind — you’re on fire!",
            "achievement_class": "continuous_practice",
            "metadata": {
                "streak_days": 50,
                "metric": "daily_test_streak",
                "event": "streak_reached",
            },
        },
        {
            "name": "Blazing Focus",
            "description": "You’ve crushed two and a half months of daily practice!",
            "achievement_class": "continuous_practice",
            "metadata": {
                "streak_days": 75,
                "metric": "daily_test_streak",
                "event": "streak_reached",
            },
        },
        {
            "name": "Ultimate Streaker",
            "description": "100-day streak — the ultimate consistency badge!",
            "achievement_class": "continuous_practice",
            "metadata": {
                "streak_days": 100,
                "metric": "daily_test_streak",
                "event": "streak_reached",
            },
        },
        {
            "name": "Study Soldier I",
            "description": "Scored 80–84% in 3 tests. Keep the momentum!",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 80,
                "score_band_max": 84,
                "number_of_tests": 3,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Soldier II",
            "description": "Scored 80–84% in 10 tests. Solid effort!",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 80,
                "score_band_max": 84,
                "number_of_tests": 10,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Soldier III",
            "description": "Scored 80–84% in 20 tests. You're building strength!",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 80,
                "score_band_max": 84,
                "number_of_tests": 20,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Soldier IV",
            "description": "Scored 80–84% in 50 tests. You're battle-tested!",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 80,
                "score_band_max": 84,
                "number_of_tests": 50,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Super Soldier",
            "description": "Scored 80–84% in 80 tests. A true master of consistency!",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 80,
                "score_band_max": 84,
                "number_of_tests": 80,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Titan I",
            "description": "Scored 85–89% in 3 tests. Strong command—you're standing tall in mastery.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 85,
                "score_band_max": 89,
                "number_of_tests": 3,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Titan II",
            "description": "Scored 85–89% in 10 tests. You're crushing near-top scores with ease.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 85,
                "score_band_max": 89,
                "number_of_tests": 10,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Titan III",
            "description": "Scored 85–89% in 20 tests. Your consistency is elite—greatness in sight.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 85,
                "score_band_max": 89,
                "number_of_tests": 20,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Titan IV",
            "description": "Scored 85–89% in 50 tests. A force to reckon with across subjects.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 85,
                "score_band_max": 89,
                "number_of_tests": 50,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Ninja I",
            "description": "Scored 90–94% in 3 tests. Silent, swift, and sharp—you're mastering the shadows.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 90,
                "score_band_max": 94,
                "number_of_tests": 3,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Ninja II",
            "description": "Scored 90–94% in 10 tests. You strike with elite speed and accuracy.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 90,
                "score_band_max": 94,
                "number_of_tests": 10,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Ninja III",
            "description": "Scored 90–94% in 20 tests. Precision and stealth define your progress.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 90,
                "score_band_max": 94,
                "number_of_tests": 20,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Ninja IV",
            "description": "Scored 90–94% in 50 tests. Your training is unmatched—master of the unseen.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 90,
                "score_band_max": 94,
                "number_of_tests": 50,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Super Ninja",
            "description": "Scored 90–94% in 80 tests. A silent force—undeniable excellence in every move.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 90,
                "score_band_max": 94,
                "number_of_tests": 80,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Hacker I",
            "description": "Scored 95–99% in 3 tests. You’ve cracked the code—next-level precision unlocked.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 95,
                "score_band_max": 99,
                "number_of_tests": 3,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Hacker II",
            "description": "Scored 95–99% in 10 tests. Every test is a system, and you're breaching them all.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 95,
                "score_band_max": 99,
                "number_of_tests": 10,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Hacker III",
            "description": "Scored 95–99% in 20 tests. Learning is your domain—you dominate every challenge.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 95,
                "score_band_max": 99,
                "number_of_tests": 20,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Hacker IV",
            "description": "Scored 95–99% in 50 tests. Precision is now your second language.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 95,
                "score_band_max": 99,
                "number_of_tests": 50,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Super Hacker",
            "description": "Scored 95–99% in 80 tests. You’ve achieved elite mastery—an unstoppable learning force.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 95,
                "score_band_max": 99,
                "number_of_tests": 80,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        # 100% band achievements (duplicate names – we auto-suffix below)
        {
            "name": "Study Hacker I",
            "description": "Scored 100% in 3 tests. Flawless start — you're coding mastery into every move.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 100,
                "score_band_max": 100,
                "number_of_tests": 3,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Hacker II",
            "description": "Scored 100% in 10 tests. Precision and power — you're mastering every subject.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 100,
                "score_band_max": 100,
                "number_of_tests": 10,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Hacker III",
            "description": "Scored 100% in 20 tests. Laser focus— you're on another level of academic skill.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 100,
                "score_band_max": 100,
                "number_of_tests": 20,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Study Hacker IV",
            "description": "Scored 100% in 50 tests. Unstoppable — your accuracy is off the charts.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 100,
                "score_band_max": 100,
                "number_of_tests": 50,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
        {
            "name": "Super Hacker",
            "description": "Scored 100% in 80 tests. You're the ultimate legend — mastery executed to perfection.",
            "achievement_class": "mastery_level",
            "metadata": {
                "score_band_min": 100,
                "score_band_max": 100,
                "number_of_tests": 80,
                "metric": "tests_scored_within_band_total",
                "scope": "all_subjects",
            },
        },
    ]

    def _dedupe_name(name: str, meta: dict, seen: dict) -> str:
        if name not in seen:
            seen[name] = 0
            return name

        seen[name] += 1
        # Prefer a semantic suffix for the 100% mastery duplicates.
        if meta.get("score_band_min") == 100 and meta.get("score_band_max") == 100:
            return f"{name} (100%)"

        # Fallback: deterministic numeric suffix.
        return f"{name} ({seen[name] + 1})"

    now = datetime.now(timezone.utc)
    seen_names = {}
    rows = []
    for ach in achievements:
        meta = ach.get("metadata") or {}
        deduped_name = _dedupe_name(ach["name"], meta, seen_names)
        rows.append(
            {
                "name": deduped_name,
                "description": ach["description"],
                "image_url": "",
                "requirements": json.dumps(meta, ensure_ascii=False),
                "achievement_class": ach.get("achievement_class"),
                "is_deleted": False,
                "created_at": now,
                "updated_at": now,
            }
        )

    op.bulk_insert(achievement_table, rows)


def downgrade():
    # This migration is a deliberate reset. Downgrade clears the newly seeded data.
    op.execute(sa.text("DELETE FROM student_has_achievement"))
    op.execute(sa.text("DELETE FROM achievement"))
