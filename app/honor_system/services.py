from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.integrations.mailer import mailer
from app.integrations.pusher import pusher
from app.notifications.operations import notification_manager, recipient_manager
from app._shared.schemas import UserTypes
from app.app_admin.models import Subject
from app.staff.models import Staff
from app.student.models import Student
from app.test.models import Test


@dataclass(frozen=True)
class AntiCheatConfig:
    grace_ms: int = 5000
    suspicious_single_event_ms: int = 15000
    auto_end_max_events: int = 3
    auto_end_total_outside_ms: int = 30000

    cheating_pattern_window_days: int = 7
    cheating_pattern_min_suspicious_tests: int = 3

    honor_vibes_total_outside_ms: int = 10000
    honor_vibes_max_events: int = 1
    honor_vibes_avg_score_min: float = 80.0
    honor_vibes_avg_score_lookback: int = 5
    honor_vibes_streak_min: int = 7
    honor_vibes_tests_per_week_min: int = 5

    # notification spam guard
    notification_dedupe_hours: int = 24


class HonorSystemService:
    """Evaluates anti-cheat + teacher notifications after a test is submitted."""

    ALERT_TYPE_CHEATING = "cheating_alert"
    ALERT_TYPE_HONOR_VIBES = "honor_vibes"

    def __init__(self, config: Optional[AntiCheatConfig] = None):
        self.config = config or AntiCheatConfig()

    # ---------------------------
    # Anti-cheat evaluation
    # ---------------------------

    def evaluate_test_meta(self, meta: Dict) -> Dict:
        """Return normalized anti-cheat metrics + flags.

        Expected meta keys (sent by frontend):
          - out_time (ms) OR outside_time_ms
          - outside_events (count)
          - max_outside_event_ms (ms)
        """

        if not isinstance(meta, dict):
            meta = {}

        outside_time_ms = meta.get("outside_time_ms")
        if outside_time_ms is None:
            outside_time_ms = meta.get("out_time")
        outside_time_ms = int(outside_time_ms or 0)

        outside_events = int(meta.get("outside_events") or 0)
        max_event_ms = int(meta.get("max_outside_event_ms") or 0)

        penalty_flag = max_event_ms >= self.config.suspicious_single_event_ms

        should_auto_end = (
            outside_events >= self.config.auto_end_max_events
            or outside_time_ms >= self.config.auto_end_total_outside_ms
        )

        is_suspicious = penalty_flag or should_auto_end

        return {
            "outside_time_ms": outside_time_ms,
            "outside_events": outside_events,
            "max_outside_event_ms": max_event_ms,
            "penalty_flag": penalty_flag,
            "should_auto_end": should_auto_end,
            "is_suspicious": is_suspicious,
        }

    # ---------------------------
    # Teacher notifications
    # ---------------------------

    def notify_if_needed(self, test: Test, student: Student) -> None:
        """Best-effort notifications. Never raises."""
        try:
            self._notify_cheating_pattern_if_needed(test, student)
        except Exception:
            pass

        try:
            self._notify_honor_vibes_if_needed(test, student)
        except Exception:
            pass

    def _get_subject_staff_recipients(self, school_id: int, subject_id: int) -> List[Staff]:
        # subject teachers in same school, approved
        return (
            Staff.query.filter_by(
                school_id=school_id,
                is_deleted=False,
                is_approved=True,
            )
            .filter(Staff.subjects.any(Subject.id == subject_id))
            .all()
        )

    def _is_duplicate_notification(self, recipient_id: int, alert_type: str, student_id: int, subject_id: int) -> bool:
        """Avoid spamming: if a similar notification exists within the dedupe window."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.config.notification_dedupe_hours)
        # Use Notification table directly to avoid circular imports in some setups
        from app.notifications.models import Notification

        recent = (
            Notification.query.filter(
                Notification.recipient_id == recipient_id,
                Notification.alert_type == alert_type,
                Notification.created_at >= cutoff,
            )
            .order_by(Notification.created_at.desc())
            .all()
        )

        # Attachments is JSON; we do a python check.
        for n in recent:
            att = n.attachments or {}
            if (
                isinstance(att, dict)
                and att.get("student_id") == student_id
                and att.get("subject_id") == subject_id
            ):
                return True
        return False

    def _notify_cheating_pattern_if_needed(self, test: Test, student: Student) -> None:
        meta = test.meta or {}
        metrics = self.evaluate_test_meta(meta)
        if not metrics["is_suspicious"]:
            return

        # Pattern across multiple tests
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.config.cheating_pattern_window_days)
        recent_tests = (
            Test.query.filter(
                Test.student_id == student.id,
                Test.is_completed == True,
                Test.created_at >= cutoff,
                Test.is_deleted == False,
            )
            .order_by(Test.created_at.desc())
            .all()
        )

        suspicious_count = 0
        for t in recent_tests:
            tmeta = t.meta or {}
            if self.evaluate_test_meta(tmeta).get("is_suspicious"):
                suspicious_count += 1

        if suspicious_count < self.config.cheating_pattern_min_suspicious_tests:
            return

        staff_list = self._get_subject_staff_recipients(student.school_id, test.subject_id)
        if not staff_list:
            return

        title = "Possible cheating detected"
        content = (
            f"{student.first_name} {student.surname} has shown suspicious behavior in "
            f"{suspicious_count} tests in the last {self.config.cheating_pattern_window_days} days."
        )
        attachments = {
            "student_id": student.id,
            "subject_id": test.subject_id,
            "suspicious_tests": suspicious_count,
        }

        for staff in staff_list:
            recipient = recipient_manager.get_recipient_by_email(staff.email, UserTypes.staff)
            if not recipient:
                recipient = recipient_manager.create_recipient(UserTypes.staff, [], staff.email, None)

            if self._is_duplicate_notification(recipient.id, self.ALERT_TYPE_CHEATING, student.id, test.subject_id):
                continue

            notification_manager.create_notification(
                title=title,
                content=content,
                alert_type=self.ALERT_TYPE_CHEATING,
                recipient_id=recipient.id,
                school_id=student.school_id,
                attachments=attachments,
            )
            pusher.notify_devices(title=title, content=content, emails=[staff.email], device_ids=recipient.device_ids)

            # email (best-effort)
            try:
                html = mailer.generate_email_text(
                    "cheating_alert.html",
                    {
                        "student": student,
                        "subject_id": test.subject_id,
                        "suspicious_tests": suspicious_count,
                        "window_days": self.config.cheating_pattern_window_days,
                    },
                )
                mailer.send_email(
                    recipients=[staff.email],
                    subject=title,
                    text=html,
                    html=True,
                )
            except Exception:
                pass

    def _notify_honor_vibes_if_needed(self, test: Test, student: Student) -> None:
        # Evaluate honor vibes on the just-submitted test context
        meta = test.meta or {}
        metrics = self.evaluate_test_meta(meta)

        if metrics["outside_time_ms"] > self.config.honor_vibes_total_outside_ms:
            return
        if metrics["outside_events"] > self.config.honor_vibes_max_events:
            return

        # score threshold: avg over last 5 tests
        recent_tests = (
            Test.query.filter(
                Test.student_id == student.id,
                Test.is_completed == True,
                Test.is_deleted == False,
            )
            .order_by(Test.created_at.desc())
            .limit(self.config.honor_vibes_avg_score_lookback)
            .all()
        )
        if len(recent_tests) < self.config.honor_vibes_avg_score_lookback:
            return
        avg_score = sum(float(t.score_acquired or 0) for t in recent_tests) / len(recent_tests)
        if avg_score < self.config.honor_vibes_avg_score_min:
            return

        # practice: streak or tests/week
        streak = int(getattr(student, "current_streak", 0) or 0)
        if streak < self.config.honor_vibes_streak_min:
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            week_tests = (
                Test.query.filter(
                    Test.student_id == student.id,
                    Test.is_completed == True,
                    Test.is_deleted == False,
                    Test.created_at >= cutoff,
                ).count()
            )
            if week_tests < self.config.honor_vibes_tests_per_week_min:
                return

        staff_list = self._get_subject_staff_recipients(student.school_id, test.subject_id)
        if not staff_list:
            return

        title = "Honor student vibes"
        content = (
            f"{student.first_name} {student.surname} is showing strong focus + performance: "
            f"avg {avg_score:.1f}% over last {self.config.honor_vibes_avg_score_lookback} tests with minimal tab switching."
        )
        attachments = {
            "student_id": student.id,
            "subject_id": test.subject_id,
            "avg_score": round(avg_score, 2),
        }

        for staff in staff_list:
            recipient = recipient_manager.get_recipient_by_email(staff.email, UserTypes.staff)
            if not recipient:
                recipient = recipient_manager.create_recipient(UserTypes.staff, [], staff.email, None)

            if self._is_duplicate_notification(recipient.id, self.ALERT_TYPE_HONOR_VIBES, student.id, test.subject_id):
                continue

            notification_manager.create_notification(
                title=title,
                content=content,
                alert_type=self.ALERT_TYPE_HONOR_VIBES,
                recipient_id=recipient.id,
                school_id=student.school_id,
                attachments=attachments,
            )
            pusher.notify_devices(title=title, content=content, emails=[staff.email], device_ids=recipient.device_ids)

            try:
                html = mailer.generate_email_text(
                    "honor_vibes.html",
                    {
                        "student": student,
                        "subject_id": test.subject_id,
                        "avg_score": round(avg_score, 2),
                    },
                )
                mailer.send_email(
                    recipients=[staff.email],
                    subject=title,
                    text=html,
                    html=True,
                )
            except Exception:
                pass
