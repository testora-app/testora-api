"""seed_seedDataForAchievements

Revision ID: 1a1eb85b8313
Revises: 322af3c44995
Create Date: 2025-07-05 21:03:31.914454

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Boolean


# revision identifiers, used by Alembic.
revision = '1a1eb85b8313'
down_revision = '322af3c44995'
branch_labels = None
depends_on = None


achievement_data = [
    # Milestone-Based
    ("First Step", "Completed your very first test"),
    ("Steady Start", "Completed 5 tests"),
    ("Practice Champ", "Completed 10 tests"),
    ("Quarter Milestone", "Completed 25 tests"),
    ("Halfway Hero", "Completed 50 tests"),
    ("Test Marathoner", "Completed 100 tests"),
    ("Comeback Streak", "Practiced 3 days in a row"),
    ("Study Warrior", "Practiced 7 days in a row"),
    ("Weekly Mastery", "Practiced every weekday this week"),
    ("Determined Learner", "Completed a test in every subject at least once"),

    # Performance-Based
    ("80 Club", "Scored 80% or more in any test"),
    ("Top Scorer", "Scored 100% in a test"),
    ("On the Rise", "Improved by 30% over last test"),
    ("Fast Learner", "Completed test under time with >90%"),
    ("Precision Player", "Scored above 90% 3 times in a row"),
    ("Rising Star", "Scored above 50% in 5 different tests"),
    ("Accuracy Master", "Less than 2 wrong answers in a 20-question test"),
    ("Consistency King", "Scored 70%+ in 5 consecutive tests"),
    ("Comeback Kid", "Failed a test, then scored >80% in retry"),
    ("Top Percentile", "Ranked in top 10% among students"),

    # Subject-Based
    ("Math Explorer", "Completed 3 Math tests at Level 1"),
    ("Science Climber", "Completed 3 Science tests at Level 2"),
    ("Language Starter", "Scored >70% in English test Level 1"),
    ("Math Strategist", "Scored 90% in Math test Level 3"),
    ("Social Studies Sleuth", "Completed 2 Social Studies Level 2 tests"),
    ("Grammar Guru", "Completed 3 English tests with 80%+ accuracy"),
    ("Science Thinker", "Scored 85%+ in Science test Level 3"),
    ("RME Reflector", "Completed 3 RME Level 1 tests"),
    ("Math Level Up", "Reached Level 5 in Math"),
    ("Multi-Subject Pro", "Reached Level 3 in 3 different subjects"),
]

def upgrade():
    achievement_table = table(
        'achievement',
        column('name', String),
        column('description', String),
        column('image_url', String),
        column('achievement_class', String),
        column('is_deleted', Boolean),
    )

    conn = op.get_bind()
    existing_names = {row[0] for row in conn.execute(sa.text("SELECT name FROM achievement")).fetchall()}

    new_rows = []
    for name, description in achievement_data:
        if name not in existing_names:
            if "Completed" in description:
                achievement_class = "Milestone"
            elif "Scored" in description or "Ranked" in description:
                achievement_class = "Performance"
            else:
                achievement_class = "Subject"
            new_rows.append({
                "name": name,
                "description": description,
                "image_url": "",
                "achievement_class": achievement_class,
                "is_deleted": False
            })

    if new_rows:
        op.bulk_insert(achievement_table, new_rows)

def downgrade():
    for name, _ in achievement_data:
        op.execute(
            sa.text("DELETE FROM achievement WHERE name = :name")
            .bindparams(name=name)
        )
