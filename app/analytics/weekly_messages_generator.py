from enum import Enum
import random
from datetime import datetime, timezone

class GoalMetric(str, Enum):
    xp = "xp"
    streak_days = "streak_days"
    topic = "topic_mastery"

class GoalStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    achieved = "achieved"
    expired = "expired"

class PerfTier(str, Enum):
    outstanding = "outstanding"
    on_track = "on_track"
    needs_nudge = "needs_nudge"
    falling_behind = "falling_behind"

def _tier_from_progress(progress: int, target: int, week_progress: float | None = None) -> PerfTier:
    if target <= 0:
        return PerfTier.on_track
    pct = progress / target
    # Optional pace adjustment: if late in week and pct < week_progress, bump tier down one.
    if week_progress is not None and pct < week_progress - 0.15:
        # penalize by one tier
        if pct >= 0.6: return PerfTier.needs_nudge
        if pct >= 0.3: return PerfTier.falling_behind
        return PerfTier.falling_behind

    if pct >= 0.9: return PerfTier.outstanding
    if pct >= 0.6: return PerfTier.on_track
    if pct >= 0.3: return PerfTier.needs_nudge
    return PerfTier.falling_behind

class GoalMessageGenerator:
    """Performance-aware messages for goal progress & achievement."""

    # -------- Achievement templates (metric-specific) --------
    ACHIEVE = {
        GoalMetric.xp: {
            PerfTier.outstanding: [
                "Phenomenal! You smashed your XP target 🎉",
                "XP goal crushed! Pure momentum 🔥",
            ],
            PerfTier.on_track: [
                "Great job! You hit your XP goal 🙌",
                "Nice work—XP target achieves! 🌟",
            ],
            PerfTier.needs_nudge: [
                "XP goal reached—way to push through! Keep the rhythm going 💪",
            ],
            PerfTier.falling_behind: [
                "You made it! XP target achieved—let's build from here 🚀",
            ],
        },
        GoalMetric.streak_days: {
            PerfTier.outstanding: [
                "Epic streak! {value} days in a row—unreal consistency 💥",
                "Legendary focus—{value}-day practice streak! 🏆",
            ],
            PerfTier.on_track: [
                "Streak unlocked: {value} days! Keep that heat 🔥",
            ],
            PerfTier.needs_nudge: [
                "Nice! {value}-day streak achieved—let's stack another 📆",
            ],
            PerfTier.falling_behind: [
                "Streak reached—great bounce back! Ready for the next one? 💫",
            ],
        },
        GoalMetric.topic: {
            PerfTier.outstanding: [
                'Mastered "{topic}" with style—onto the next boss level 🎯',
            ],
            PerfTier.on_track: [
                '“{topic}” mastered—excellent progress! 🌟',
            ],
            PerfTier.needs_nudge: [
                'You nailed “{topic}”—confidence unlocked ✅',
            ],
            PerfTier.falling_behind: [
                '“{topic}” done! Small wins become big wins—keep going 🚀',
            ],
        },
    }

    # -------- Progress templates (metric + tier) --------
    PROGRESS = {
        GoalMetric.xp: {
            PerfTier.outstanding: [
                "{progress}/{target} XP in {subject}—you're flying! Only {remaining} to spare ✨",
                "Almost there: {progress}/{target} XP in {subject}. Finish strong 💪",
            ],
            PerfTier.on_track: [
                "{progress}/{target} XP in {subject}—right on track!",
                "Solid pace: {progress}/{target} XP. Keep the flow 🔁",
            ],
            PerfTier.needs_nudge: [
                "{progress}/{target} XP so far. Try one more quick set today—just {remaining} to go!",
                "You've got this: {progress}/{target} XP. A short session can move the needle 🎯",
            ],
            PerfTier.falling_behind: [
                "Let's spark it up: start with a 10-minute {subject} drill. {remaining} XP to the goal ⚡",
                "Slow start—but totally doable. Aim for a small session now. {remaining} XP left.",
            ],
        },
        GoalMetric.streak_days: {
            PerfTier.outstanding: [
                "Streak is hot: {progress}/{target} days! Keep the chain alive 🔗",
            ],
            PerfTier.on_track: [
                "{progress}/{target} streak days—nice rhythm! 📆",
            ],
            PerfTier.needs_nudge: [
                "You're at {progress} day(s). A quick practice today keeps the streak going ✅",
            ],
            PerfTier.falling_behind: [
                "No worries—start a streak today. {target} day goal within reach 🌱",
            ],
        },
    }

    # -------- Public API --------
    @classmethod
    def achievement(cls, metric: GoalMetric, subject=None, topic=None, value=None,
                    target=None, progress=None, week_progress: float | None = None):
        """
        Achievement message with tone based on performance vs target & pace.
        For streak/topic, pass `value` (e.g., 5-day streak). For XP, pass target/progress too.
        """
        # Derive tier from final run (helps differentiate an easy win vs dominant performance)
        if metric == GoalMetric.xp and target is not None and progress is not None:
            tier = _tier_from_progress(progress, target, week_progress)
        else:
            # Default to on_track if no ratio to compute
            tier = PerfTier.on_track

        templates = cls.ACHIEVE.get(metric, {}).get(tier) or ["Goal achieved—great work!"]
        t = random.choice(templates)
        return t.format(subject=subject or "your subject",
                        topic=topic or "",
                        value=value if value is not None else "",
                        target=target if target is not None else "",
                        progress=progress if progress is not None else "",
                        remaining=max(0, (target or 0) - (progress or 0)))

    @classmethod
    def progress(cls, metric: GoalMetric, progress: int, target: int,
                 subject=None, week_progress: float | None = None):
        """
        Progress/nudge message tuned by performance tier and pace in the week.
        week_progress: 0..1 (e.g., Wednesday night ≈ 0.5–0.6)
        """
        remaining = max(0, target - progress)
        tier = _tier_from_progress(progress, target, week_progress)
        templates = cls.PROGRESS.get(metric, {}).get(tier) or ["Keep going—you're doing great!"]
        t = random.choice(templates)
        return t.format(progress=progress, target=target, remaining=remaining, subject=subject or "this subject")

    @staticmethod
    def weekly_summary(items: list[str]):
        header = "🎉 Weekly Wins Celebration!"
        bullet = "\n".join(f"• {s}" for s in items)
        footer = "Keep shining, you're doing amazing! ✨"
        return f"{header}\n\n{bullet}\n\n{footer}"

    @staticmethod
    def payload(message: str, variant: str = "info", icon: str = "trophy"):
        """Optional: standardize UI payloads."""
        return {
            "title": "Weekly Update" if variant != "success" else "Goal Achieved!",
            "message": message,
            "variant": variant,  # info | success | warning | danger
            "icon": icon,        # e.g., trophy, sparkles, fire
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
