# models.py
from datetime import datetime
from enum import Enum
from sqlalchemy import UniqueConstraint, Index, CheckConstraint, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum, JSONB

from app.extensions import db
from app._shared.models import BaseModel

# --- Enums ---
class GoalStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    achieved = "achieved"
    expired = "expired"

class GoalMetric(str, Enum):
    xp = "xp"
    streak_days = "streak_days"

# --- Model ---
class WeeklyGoal(BaseModel):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_id = db.Column(db.BigInteger, nullable=False, index=True)
    subject_id = db.Column(db.BigInteger, nullable=True)  # NULL = subject-agnostic
    week_start_date = db.Column(db.Date, nullable=False)  # Monday in Africa/Accra

    status = db.Column(
        PGEnum(GoalStatus, name="goal_status", create_type=False),
        nullable=False,
        default=GoalStatus.pending,
        server_default=GoalStatus.pending.value,
    )

    target_metric = db.Column(
        PGEnum(GoalMetric, name="goal_metric", create_type=False),
        nullable=False,
    )
    target_value = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    current_value = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    params = db.Column(JSONB, nullable=False, default=dict, server_default="{}")
    achieved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Constraints & indexes
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "week_start_date", "target_metric",
                         name="uniq_weekly_goal"),
        CheckConstraint("target_value >= 0", name="ck_target_value_nonneg"),
        CheckConstraint("current_value >= 0", name="ck_current_value_nonneg"),
        Index("idx_weekly_goals_student_week", "student_id", "week_start_date"),
        Index("idx_weekly_goals_status", "status"),
    )

    # --- Small helpers (optional, safe) ---
    def apply_progress(self, delta: int) -> None:
        """Increment current_value and update status/achieved_at accordingly."""
        if delta is None or delta <= 0:
            return
        self.current_value = (self.current_value or 0) + int(delta)
        if self.current_value > 0 and self.status == GoalStatus.pending:
            self.status = GoalStatus.in_progress
        if self.current_value >= self.target_value and self.status != GoalStatus.achieved:
            self.status = GoalStatus.achieved
            self.achieved_at = datetime.utcnow()

    def set_value(self, value: int) -> None:
        """Idempotent setter (e.g., after recomputing from attempts)."""
        value = max(0, int(value))
        self.current_value = value
        if value == 0 and self.status == GoalStatus.pending:
            return
        if value > 0 and self.status == GoalStatus.pending:
            self.status = GoalStatus.in_progress
        if value >= self.target_value:
            if self.status != GoalStatus.achieved:
                self.status = GoalStatus.achieved
                self.achieved_at = datetime.utcnow()
        else:
            # keep in_progress if previously achieved is not true anymore (shouldn't happen if setter is used sensibly)
            if self.status == GoalStatus.achieved:
                self.status = GoalStatus.in_progress
                self.achieved_at = None
