import calendar
from datetime import datetime, timezone
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Any, Optional, Iterable

from apiflask.exceptions import HTTPError

from app.student.operations import student_manager, batch_manager
from app.test.operations import test_manager
from app.app_admin.operations import subject_manager
from app.student.operations import student_manager
from app.app_admin.operations import topic_manager
from app.analytics.operations import ssr_manager, sts_manager
from app.achievements.operations import student_has_achievement_manager


class AnalyticsService:

    performance_bands = {
        "highly_proficient": 80,
        "proficient": 70,
        "approaching_proficient": 65,
        "developing": 50,
        "emerging": 0,
    }

    def _to_datetime(self, val: Any) -> Optional[datetime]:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, (int, float)):  # unix seconds
            return datetime.fromtimestamp(val, tz=timezone.utc)
        if isinstance(val, str):
            s = val.strip()
            if s.endswith("Z"):  # ISO 8601 with Z
                s = s[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(s)
            except ValueError:
                pass
        return None

    def most_recent_created_at(
        self, items: Iterable[Any], key: str = "created_at"
    ) -> Optional[datetime]:
        """
        Returns the latest `created_at` as a datetime, or None if none parse.
        Each item can be a dict or an object with an attribute named `key`.
        """
        latest = None
        for it in items:
            raw = it.get(key) if isinstance(it, dict) else getattr(it, key, None)
            dt = self._to_datetime(raw)
            if dt is not None and (latest is None or dt > latest):
                latest = dt
        return latest

    def get_performance_band(self, score):
        for band, threshold in sorted(
            self.performance_bands.items(), key=lambda kv: kv[1], reverse=True
        ):
            if score >= threshold:
                return band
        return "emerging"

    def get_time_range(self, time_range):
        if time_range == "this_week":
            return (
                datetime.now(timezone.utc).isocalendar().week,
                datetime.now(timezone.utc).isocalendar().year,
            )
        elif time_range == "this_month":
            return datetime.now(timezone.utc).month, datetime.now(timezone.utc).year
        elif time_range == "all_time":
            return None, None

    def get_last_time_range(self, time_range):
        if time_range == "this_week":
            return (
                datetime.now(timezone.utc).isocalendar().week - 1,
                datetime.now(timezone.utc).isocalendar().year,
            )
        elif time_range == "this_month":
            return datetime.now(timezone.utc).month - 1, datetime.now(timezone.utc).year
        elif time_range == "all_time":
            return None, None

    def count_in_range(
        self,
        records: List[Dict[str, Any]],
        min_times: int,
        max_times: int,
        id_key: str = "student_id",
    ) -> Tuple[int, float]:
        """
        Returns:
          - number of objects whose student_id appears between [min_times, max_times] (inclusive)
          - percentage of such objects out of all objects (0–100)
        """
        if not records:
            return 0, 0.0

        if not isinstance(records[0], dict):
            records = [r.to_json() for r in records]

        if min_times > max_times:
            min_times, max_times = max_times, min_times

        counts = Counter(r.get(id_key) for r in records if id_key in r)

        qualifying_ids = {
            sid for sid, c in counts.items() if min_times <= c <= max_times
        }

        qualifying_objects = sum(1 for r in records if r.get(id_key) in qualifying_ids)
        pct = (qualifying_objects / len(records)) * 100
        return qualifying_objects, round(pct, 2)

    def configure_performance_requirements(
        self, school_id, batch_id, time_range, subject_id=None
    ):
        week, year = self.get_time_range(time_range)
        last_week, last_year = self.get_last_time_range(time_range)

        all_students = student_manager.get_active_students_by_school(school_id)
        all_student_ids = [student.id for student in all_students]

        # get the batch in question
        if batch_id:
            batch = batch_manager.get_batch_by_id(batch_id)
            if not batch:
                raise HTTPError(status_code=404, detail="Batch not found")
            students = batch.to_json()["students"]
            student_ids = [student["id"] for student in students]
        else:
            student_ids = all_student_ids

        # now get the tests by the subject_id  and student_ids
        this_tests = test_manager.get_tests_by_student_ids(student_ids)

        if subject_id:
            this_tests = [test for test in this_tests if test.subject_id == subject_id]

        # filter the tests by the time range
        if week and year and time_range == "this_week":
            this_tests = [
                test
                for test in this_tests
                if test.created_at.isocalendar().week == week
                and test.created_at.isocalendar().year == year
            ]
        elif week and year and time_range == "this_month":
            this_tests = [
                test
                for test in this_tests
                if test.created_at.month == week and test.created_at.year == year
            ]
        else:
            this_tests = this_tests

        # now get the last week or month
        if last_week and last_year and time_range == "this_week":
            last_tests = [
                test
                for test in this_tests
                if test.created_at.isocalendar().week == last_week
                and test.created_at.isocalendar().year == last_year
            ]
        elif last_week and last_year and time_range == "this_month":
            last_tests = [
                test
                for test in this_tests
                if test.created_at.month == last_week
                and test.created_at.year == last_year
            ]
        else:
            last_tests = this_tests

        if subject_id:
            last_tests = [test for test in last_tests if test.subject_id == subject_id]

        return this_tests, last_tests, student_ids

    def get_practice_rate(
        self, school_id, batch_id, time_range, subject_id=None
    ) -> Dict[str, Any]:
        this_tests, last_tests, all_student_ids = (
            self.configure_performance_requirements(
                school_id, batch_id, time_range, subject_id
            )
        )

        total_students = len(all_student_ids)
        if total_students == 0:
            # No students – return an all-zero structure
            return {
                "number_of_tests_per_student": 0,
                "comparison": 0,
                "practiced_number": 0,
                "practiced_percent": 0.0,
                "not_practiced_number": 0,
                "not_practiced_percent": 0.0,
                "tier_distribution": {
                    "no_practice": {"number": 0, "percent": 0.0},
                    "minimal_practice": {"number": 0, "percent": 0.0},
                    "consistent_practice": {"number": 0, "percent": 0.0},
                    "high_practice": {"number": 0, "percent": 0.0},
                },
            }

        # --- Current vs previous participation (student-based) ---
        these_students_took_tests_this_param = set(t.student_id for t in this_tests)
        these_students_took_tests_last_param = set(t.student_id for t in last_tests)

        number_of_tests_per_student = (
            round(len(this_tests) / total_students, 2) if total_students > 0 else 0
        )

        current = len(these_students_took_tests_this_param)
        previous = len(these_students_took_tests_last_param)

        if previous > 0:
            comparison = (
                current - previous
            ) / previous  # growth rate (e.g. 0.2 = +20%)
        else:
            comparison = 0  # or None if you want "no baseline" instead

        # --- Overall practice vs no practice (student-based) ---
        practiced_number = current
        practiced_percent = (practiced_number / total_students) * 100

        not_practiced_number = total_students - practiced_number
        not_practiced_percent = 100 - practiced_percent

        # --- Tier distributions (student-based) ---
        # Count how many tests each student took in THIS period
        test_counts = Counter(t.student_id for t in this_tests)

        def count_students_in_range(
            counts: Counter, min_times: int, max_times: int
        ) -> int:
            return sum(1 for c in counts.values() if min_times <= c <= max_times)

        minimal_students = count_students_in_range(test_counts, 1, 2)
        consistent_students = count_students_in_range(test_counts, 3, 5)
        high_students = count_students_in_range(test_counts, 6, 10**9)

        minimal_practice_number = minimal_students
        minimal_practice_percent = (
            minimal_students / total_students * 100 if total_students > 0 else 0.0
        )

        consistent_practice_number = consistent_students
        consistent_practice_percent = (
            consistent_students / total_students * 100 if total_students > 0 else 0.0
        )

        high_practice_number = high_students
        high_practice_percent = (
            high_students / total_students * 100 if total_students > 0 else 0.0
        )

        tier_distribution = {
            "no_practice": {
                "number": not_practiced_number,
                "percent": round(not_practiced_percent, 2),
            },
            "minimal_practice": {
                "number": minimal_practice_number,
                "percent": round(minimal_practice_percent, 2),
            },
            "consistent_practice": {
                "number": consistent_practice_number,
                "percent": round(consistent_practice_percent, 2),
            },
            "high_practice": {
                "number": high_practice_number,
                "percent": round(high_practice_percent, 2),
            },
        }

        return {
            "number_of_tests_per_student": number_of_tests_per_student,
            "change_from": round(previous, 2) if previous is not None else previous,
            "change_direction": "up" if comparison > 0 else "down",
            "comparison": (
                round(comparison * 100, 2) if comparison is not None else comparison
            ),
            "practiced_number": practiced_number,
            "practiced_percent": round(practiced_percent, 2),
            "not_practiced_number": not_practiced_number,
            "not_practiced_percent": round(not_practiced_percent, 2),
            "tier_distribution": tier_distribution,
        }

    def calculate_student_average_performance(
        self,
        total_number_of_students: int,
        tests,
        performance_band: str,
    ):
        """
        Calculates how many students fall into a given performance band
        based on their AVERAGE score over the provided tests.

        Args:
        total_number_of_students (int): Total students in the cohort
                                        (including those with no tests)
        tests (list): List of tests within the selected time range/subject
                        Each test is expected to have .student_id and .score_acquired
        performance_band (str): Target band
                                e.g. 'highly_proficient', 'proficient',
                                'approaching_proficient', 'developing', 'emerging'

        Returns:
        dict:
            - count: number of students in that band
            - percentage: percentage of total students in that band (0–100)
        """
        # Guard: no students or no tests → nothing in this band
        if total_number_of_students == 0 or not tests:
            return {"count": 0, "percentage": 0.0}

        # Collect scores per student
        scores_by_student = defaultdict(list)
        for test in tests:
            scores_by_student[test.student_id].append(test.score_acquired)

        # Classify each student by their AVERAGE score band
        number_of_students_in_band = 0
        for student_id, scores in scores_by_student.items():
            avg_score = sum(scores) / len(scores)
            band = self.get_performance_band(avg_score)
            if band == performance_band:
                number_of_students_in_band += 1

        percentage_of_students_in_band = (
            number_of_students_in_band / total_number_of_students
        ) * 100

        return {
            "count": number_of_students_in_band,
            "percentage": round(percentage_of_students_in_band, 2),
        }

    def get_performance_distribution(
        self, school_id, batch_id, time_range, subject_id=None
    ):
        this_tests, last_tests, all_student_ids = (
            self.configure_performance_requirements(
                school_id, batch_id, time_range, subject_id
            )
        )

        # Decide which tests to use based on the time range
        if time_range == "this_week":
            tests = this_tests
        elif time_range == "last_week":
            tests = last_tests
        else:
            # e.g. "this_month", "all_time" → combine
            tests = this_tests + last_tests

        # Subject label
        if subject_id:
            subject = subject_manager.get_subject_by_id(subject_id)
            subject_name = subject.name
        else:
            subject_name = "Overall"

        total_students = len(all_student_ids)

        # If there are no students at all, return an all-zero structure
        if total_students == 0:
            return {
                "subject_name": subject_name,
                "proficiency_percent": 0.0,
                "proficiency_status": None,
                "tier_distribution": {
                    "highly_proficient": {"count": 0, "percentage": 0.0},
                    "proficient": {"count": 0, "percentage": 0.0},
                    "approaching_proficient": {"count": 0, "percentage": 0.0},
                    "developing": {"count": 0, "percentage": 0.0},
                    "emerging": {"count": 0, "percentage": 0.0},
                },
                "summary_distribution": {
                    "proficiency_above": {"count": 0, "percentage": 0.0},
                    "at_risk": {"count": 0, "percentage": 0.0},
                    "average_tests": {"value": 0.0, "unit": "tests/student"},
                    "average_time_spent": {"value": 0.0, "unit": "min/student"},
                },
                "last_updated": None,
            }

        # --- Average score across tests (0–100) ---
        if tests:
            average_score = sum(test.score_acquired for test in tests) / len(tests)
        else:
            average_score = 0.0

        proficiency_percent = round(average_score, 2)
        proficiency_status = self.get_performance_band(average_score)

        # --- Tier distribution (student-based; uses calculate_student_average_performance) ---
        tier_distribution = {
            "highly_proficient": self.calculate_student_average_performance(
                total_students, tests, "highly_proficient"
            ),
            "proficient": self.calculate_student_average_performance(
                total_students, tests, "proficient"
            ),
            "approaching_proficient": self.calculate_student_average_performance(
                total_students, tests, "approaching_proficient"
            ),
            "developing": self.calculate_student_average_performance(
                total_students, tests, "developing"
            ),
            "emerging": self.calculate_student_average_performance(
                total_students, tests, "emerging"
            ),
        }

        # --- Rollup: At/Above Proficiency vs At Risk (student-based) ---
        # At/Above Proficiency = Highly Proficient + Proficient + Approaching Proficient
        proficiency_above = (
            tier_distribution["highly_proficient"]["count"]
            + tier_distribution["proficient"]["count"]
            + tier_distribution["approaching_proficient"]["count"]
        )
        proficiency_above_percent = (
            (proficiency_above / total_students) * 100 if total_students > 0 else 0.0
        )

        # At Risk = Developing + Emerging
        at_risk = (
            tier_distribution["developing"]["count"]
            + tier_distribution["emerging"]["count"]
        )
        at_risk_percent = (
            (at_risk / total_students) * 100 if total_students > 0 else 0.0
        )

        # --- Average tests and time per student ---
        if tests:
            # average number of tests per student in this cohort
            avg_tests_per_student = len(tests) / total_students

            # average time per test in minutes
            total_seconds = sum(
                (test.finished_on - test.started_on).total_seconds() for test in tests
            )
            avg_time_minutes = (total_seconds / len(tests)) / 60.0
        else:
            avg_tests_per_student = 0.0
            avg_time_minutes = 0.0

        summary_distribution = {
            "proficiency_above": {
                "count": proficiency_above,
                "percentage": round(proficiency_above_percent, 2),
            },
            "at_risk": {
                "count": at_risk,
                "percentage": round(at_risk_percent, 2),
            },
            "average_tests": {
                "value": round(avg_tests_per_student, 2),
                "unit": "tests/student",
            },
            "average_time_spent": {
                "value": round(avg_time_minutes, 2),
                "unit": "min/student",
            },
        }

        return {
            "subject_name": subject_name,
            "proficiency_percent": proficiency_percent,
            "proficiency_status": proficiency_status,
            "tier_distribution": tier_distribution,
            "summary_distribution": summary_distribution,
            "last_updated": self.most_recent_created_at(tests),
        }

    from collections import defaultdict


    def get_subject_performance(self, school_id, batch_id, subject_id=None):
        # 1. Resolve students for this context
        if batch_id:
            batch = batch_manager.get_batch_by_id(batch_id)
            students = batch.to_json()["students"]
            student_ids = [student["id"] for student in students]
        else:
            students = student_manager.get_active_students_by_school(school_id)
            student_ids = [student.id for student in students]

        if not student_ids:
            return []

        # 2. Get all tests for these students (optionally filtered by subject)
        tests = test_manager.get_tests_by_student_ids(student_ids)
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        # 3. Decide which subjects to report on
        if subject_id:
            subject = subject_manager.get_subject_by_id(subject_id)
            subjects = [subject] if subject else []
        else:
            subjects = subject_manager.get_subject_by_curriculum("bece")

        subject_distribution = []

        for subject in subjects:
            # All tests for this subject
            subject_tests = [t for t in tests if t.subject_id == subject.id]

            if not subject_tests:
                # No data for this subject in this context
                subject_distribution.append(
                    {
                        "subject_name": subject.name,
                        "student_readiness_number": 0,
                        "student_readiness_percent": 0.0,
                        # you can decide if you want a special "no_data" status here instead
                        "status": self.get_performance_band(0),
                    }
                )
                continue

            # 4. Build per-student average score for THIS subject
            scores_by_student = defaultdict(list)
            for test in subject_tests:
                scores_by_student[test.student_id].append(test.score_acquired)

            avg_by_student = {
                sid: (sum(scores) / len(scores))
                for sid, scores in scores_by_student.items()
            }

            # 5. Classify each student by their average band
            # Assumption: "ready" = at/above proficiency
            # If you want only HP+P, adjust ready_bands accordingly.
            ready_bands = {
                "highly_proficient",
                "proficient",
                "approaching_proficient",
            }

            students_ready = [
                sid
                for sid, avg in avg_by_student.items()
                if self.get_performance_band(avg) in ready_bands
            ]

            student_readiness_number = len(students_ready)
            student_readiness_percent = (
                student_readiness_number / len(student_ids) * 100 if student_ids else 0.0
            )

            # 6. Subject status from mean of student averages (not raw tests)
            if avg_by_student:
                average_subject_score = sum(avg_by_student.values()) / len(avg_by_student)
            else:
                average_subject_score = 0.0

            status_band = self.get_performance_band(average_subject_score)

            subject_distribution.append(
                {
                    "subject_name": subject.name,
                    "student_readiness_number": student_readiness_number,
                    "student_readiness_percent": round(student_readiness_percent, 2),
                    "status": status_band,
                }
            )

            return subject_distribution

    def get_recent_tests_activities(self, school_id, batch_id, subject_id=None):
        if batch_id:
            batch = batch_manager.get_batch_by_id(batch_id)
            students = batch.to_json()["students"]
            student_ids = [student["id"] for student in students]
        else:
            students = student_manager.get_active_students_by_school(school_id)
            student_ids = [student.id for student in students]

        tests = test_manager.get_tests_by_student_ids(student_ids)
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        sorted_tests = sorted(tests, key=lambda test: test.created_at, reverse=True)[
            :10
        ]
        student_ids = [test.student_id for test in sorted_tests]
        students = student_manager.get_students_by_ids(student_ids)
        subjects = subject_manager.get_subject_by_curriculum("bece")

        student_dict = {student.id: student for student in students}
        subject_dict = {subject.id: subject for subject in subjects}

        now = datetime.now(timezone.utc)

        tests_info = []

        for test in sorted_tests:
            tests_info.append(
                {
                    "description": f"{student_dict[test.student_id].first_name} completed a test in '{subject_dict[test.subject_id].name}' ",
                    "time": test.created_at,
                    "type": "user_activity",
                }
            )

        return tests_info

    def group_students_by_proficiency(self, tests):
        student_scores = defaultdict(list)
        for test in tests:
            student_scores[test.student_id].append(test.score_acquired)

        # Step 2: calculate averages
        student_avg = {
            sid: sum(scores) / len(scores) for sid, scores in student_scores.items()
        }

        band_counts = defaultdict(int)
        for avg_score in student_avg.values():
            band = self.get_performance_band(avg_score)
            band_counts[band] += 1

        return band_counts

    def get_proficiency_distribution(self, school_id, batch_id, subject_id=None):
        if batch_id:
            batch = batch_manager.get_batch_by_id(batch_id)
            students = batch.to_json()["students"]
            student_ids = [student["id"] for student in students]
        else:
            students = student_manager.get_active_students_by_school(school_id)
            student_ids = [student.id for student in students]

        tests = test_manager.get_tests_by_student_ids(student_ids)
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        band_counts = self.group_students_by_proficiency(tests)

        total_students = len(student_ids)

        distribution = [
            {
                "name": "highly_proficient",
                "students": band_counts["highly_proficient"],
                "percentage": (
                    band_counts["highly_proficient"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "proficient",
                "students": band_counts["proficient"],
                "percentage": (
                    band_counts["proficient"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "approaching_proficient",
                "students": band_counts["approaching"],
                "percentage": (
                    band_counts["approaching"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "developing",
                "students": band_counts["developing"],
                "percentage": (
                    band_counts["developing"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "emerging",
                "students": band_counts["emerging"],
                "percentage": (
                    band_counts["emerging"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
        ]

        return distribution

    def group_average_scores_by_month(self, tests):
        month_counts = defaultdict(list)
        for test in tests:
            key = (test.created_at.year, test.created_at.month)  # (year, month)
            month_counts[key].append(test.score_acquired)
        return month_counts

    def get_average_score_trend(self, school_id, batch_id, subject_id=None):
        if batch_id:
            batch = batch_manager.get_batch_by_id(batch_id)
            students = batch.to_json()["students"]
            student_ids = [student["id"] for student in students]
        else:
            students = student_manager.get_active_students_by_school(school_id)
            student_ids = [student.id for student in students]

        tests = test_manager.get_tests_by_student_ids(student_ids)
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        average_scores = self.group_average_scores_by_month(tests)

        month_scores_named = {}
        for year, month in sorted(average_scores.keys()):
            scores = average_scores[(year, month)]
            avg_score = sum(scores) / len(scores)
            avg_score = round(avg_score, 2)  # 2 decimal places
            month_name = f"{calendar.month_name[month]} {year}"  # e.g. "January 2025"
            month_scores_named[month_name] = avg_score

        return month_scores_named

    def get_performance_general(self, school_id, batch_id, subject_id=None):
        if batch_id:
            batch = batch_manager.get_batch_by_id(batch_id)
            students = batch.to_json()["students"]
            student_ids = [student["id"] for student in students]
        else:
            students = student_manager.get_active_students_by_school(school_id)
            student_ids = [student.id for student in students]

        tests = test_manager.get_tests_by_student_ids(student_ids)
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        average_score = round(
            (
                sum(test.score_acquired for test in tests) / len(tests)
                if len(tests) > 0
                else 0
            ),
            2,
        )

        highly_proficient_students = len(
            [
                test
                for test in tests
                if self.get_performance_band(test.score_acquired) == "highly_proficient"
                and test.student_id in student_ids
            ]
        )  # filter to make sure deleted students are not part of the count

        total_students = len(student_ids)

        return {
            "average_score": average_score,
            "highly_proficient_students": highly_proficient_students,
            "total_students": total_students,
        }

    def get_students_proficiency(self, batch_id, subject_id=None):
        batch = batch_manager.get_batch_by_id(batch_id)
        students = batch.to_json()["students"]
        students_dict = {student["id"]: student for student in students}
        student_ids = [student["id"] for student in students]

        tests = test_manager.get_tests_by_student_ids(student_ids)
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        students_proficiency = []

        for student_id in student_ids:
            student_tests = [test for test in tests if test.student_id == student_id]
            students_proficiency.append(
                {
                    "student_id": student_id,
                    "student_name": students_dict[student_id]["surname"]
                    + " "
                    + students_dict[student_id]["first_name"],
                    "average_score": round(
                        (
                            sum(test.score_acquired for test in student_tests)
                            / len(student_tests)
                            if len(student_tests) > 0
                            else 0
                        ),
                        2,
                    ),
                    "batch_name": batch.batch_name,
                    "proficiency": self.get_performance_band(
                        sum(test.score_acquired for test in student_tests)
                        / len(student_tests)
                        if len(student_tests) > 0
                        else 0
                    ),
                }
            )

        return students_proficiency

    def get_practice_tier(self, total_time_spent):
        if total_time_spent == 0 or total_time_spent is None:
            return "no_practice"
        elif total_time_spent <= 60:
            return "minimal_practice"
        elif total_time_spent <= 120:
            return "consistent_practice"
        else:
            return "high_practice"

    def get_performance_indicators(self, student_id, subject_id=None, batch_id=None):
        student = student_manager.get_student_by_id(student_id)
        tests = test_manager.get_tests_by_student_ids([student_id])
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        average_score = round(
            (
                sum(test.score_acquired for test in tests) / len(tests)
                if len(tests) > 0
                else 0
            ),
            2,
        )
        proficiency = self.get_performance_band(average_score)
        total_time_spent = round(
            sum((test.finished_on - test.started_on).total_seconds() for test in tests)
            / 60,
            2,
        )
        practice_tier = self.get_practice_tier(total_time_spent)

        return {
            "student_id": student_id,
            "student_name": student.surname + " " + student.first_name,
            "average_score": average_score,
            "proficiency": proficiency,
            "total_tests_taken": len(tests),
            "practice_tier": practice_tier,
            "total_time_spent": total_time_spent,
            "average_proficiency": average_score,
        }

    def get_subject_proficiency(self, student_id, subject_id=None, batch_id=None):
        tests = test_manager.get_tests_by_student_ids([student_id])
        subject_ids = []
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]
            subject_ids.append(subject_id)
        else:
            subject_ids = [test.subject_id for test in tests]

        subjects = subject_manager.get_subject_by_curriculum("bece")

        subjects = {subject.id: subject for subject in subjects}

        subject_performance = []

        for subject_id, subject in subjects.items():
            tests = [test for test in tests if test.subject_id == subject_id]

            average_score = round(
                (
                    sum(test.score_acquired for test in tests) / len(tests)
                    if len(tests) > 0
                    else 0
                ),
                2,
            )
            proficiency = self.get_performance_band(average_score)

            subject_performance.append(
                {
                    "subject_id": subject_id,
                    "subject_name": subject.name,
                    "average_score": average_score,
                    "proficiency": proficiency,
                }
            )

        return subject_performance

    def get_test_history(self, student_id, subject_id=None, batch_id=None):
        tests = test_manager.get_tests_by_student_ids([student_id])
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        tests = sorted(tests, key=lambda test: test.created_at, reverse=True)

        subject_ids = set(test.subject_id for test in tests)
        subjects = subject_manager.get_subjects_by_ids(list(subject_ids))

        subjects = {subject.id: subject for subject in subjects}

        test_history = []
        for test in tests:
            test_history.append(
                {
                    "test_id": test.id,
                    "subject_id": test.subject_id,
                    "subject_name": subjects[test.subject_id].name,
                    "proficiency": self.get_performance_band(test.score_acquired),
                    "score": test.score_acquired,
                    "points": test.points_acquired,
                }
            )

        return test_history

    def get_proficiency_graph(self, student_id, subject_id=None, batch_id=None):
        student_topic_scores = sts_manager.select_student_topic_score_history(
            student_id
        )
        topics = topic_manager.get_topic_by_ids(
            [score.topic_id for score in student_topic_scores]
        )
        if subject_id:
            topics = [topic for topic in topics if topic.subject_id == subject_id]

        topics = {topic.id: topic for topic in topics}

        topic_bands = {}
        for score in student_topic_scores:
            if score.topic_id not in topics:
                continue

            proficiency_band = self.get_performance_band(score.score_acquired)
            if proficiency_band not in topic_bands:
                topic_bands[proficiency_band] = {"count": 0, "topics": []}

            topic_bands[proficiency_band]["count"] += 1
            topic_bands[proficiency_band]["topics"].append(topics[score.topic_id].name)

        proficiency_graph = []
        for band, data in topic_bands.items():
            proficiency_graph.append(
                {"band": band, "count": data["count"], "topics": data["topics"]}
            )

        return proficiency_graph

    def get_failing_topics(self, student_id, subject_id=None, batch_id=None):
        recommendations = ssr_manager.select_student_recommendations(student_id)
        topics = topic_manager.get_topic_by_ids(
            [recommendation.topic_id for recommendation in recommendations]
        )
        if subject_id:
            topics = [topic for topic in topics if topic.subject_id == subject_id]

        subjects = subject_manager.get_subjects_by_ids(
            [topic.subject_id for topic in topics]
        )
        subjects = {subject.id: subject for subject in subjects}

        topics = {topic.id: topic for topic in topics}

        failing_topics = []
        for recommendation in recommendations:
            failing_topics.append(
                {
                    "topic_name": topics[recommendation.topic_id].name,
                    "subject_name": subjects[
                        topics[recommendation.topic_id].subject_id
                    ].name,
                    "average_score": 0,  # TODO: calculate average score
                    "proficiency": recommendation.recommendation_level,
                }
            )

        return failing_topics

    def get_student_average_and_band(self, student_id, subject_id=None, batch_id=None):
        tests = test_manager.get_tests_by_student_ids([student_id])
        student = student_manager.get_student_by_id(student_id)
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        average_score = round(
            (
                sum(test.score_acquired for test in tests) / len(tests)
                if len(tests) > 0
                else 0
            ),
            2,
        )
        proficiency = self.get_performance_band(average_score)

        return {
            "student_id": student_id,
            "student_name": student.surname + " " + student.first_name,
            "average_score": average_score,
            "proficiency": proficiency,
        }

    def get_performance_topics(self, subject_id, batch_id=None, stage=None, level=None):
        """
        Get performance data for topics based on student_topic_scores with optional filtering.

        Args:
            stage (str, optional): Filter by stage (e.g., "Stage 1-3", "Stage 4-6", "Stage 7-9")
            level (str, optional): Filter by proficiency level (e.g., "EMERGING", "DEVELOPING", "APPROACHING_PROFICIENT", "HIGHLY_PROFICIENT")

        Returns:
            list: Filtered topic performance data
        """
        from sqlalchemy import func, distinct
        from app.analytics.models import StudentTopicScores

        # Stage mapping based on topic level
        def get_stage_from_level(topic_level):
            if topic_level <= 3:
                return "Stage 1-3"
            elif topic_level <= 6:
                return "Stage 4-6"
            else:
                return "Stage 7-9"

        # Get student IDs based on batch_id if provided
        if batch_id:
            batch = batch_manager.get_batch_by_id(batch_id)
            students = batch.to_json()["students"]
            student_ids = [student["id"] for student in students]
        else:
            student_ids = None

        # Build query with filters
        query = StudentTopicScores.query.filter_by(subject_id=subject_id)

        # Filter by student IDs if batch_id was provided
        if student_ids:
            query = query.filter(StudentTopicScores.student_id.in_(student_ids))

        # Query to get average scores and student counts per topic
        topic_stats = (
            query.with_entities(
                StudentTopicScores.topic_id,
                func.avg(StudentTopicScores.score_acquired).label("average_score"),
                func.count(distinct(StudentTopicScores.student_id)).label(
                    "students_affected"
                ),
            )
            .group_by(StudentTopicScores.topic_id)
            .all()
        )

        # Get topics for this subject to map topic_id to topic details
        topics = topic_manager.get_topic_by_subject(subject_id)
        topic_dict = {topic.id: topic for topic in topics}

        # Build performance data
        performance_data = []
        for topic_id, avg_score, student_count in topic_stats:
            if topic_id not in topic_dict:
                continue

            topic = topic_dict[topic_id]
            avg_score_rounded = round(float(avg_score), 2) if avg_score else 0

            # Get performance band using existing function
            proficiency_level = self.get_performance_band(avg_score_rounded).upper()

            # Map topic level to stage
            topic_stage = get_stage_from_level(topic.level)

            performance_data.append(
                {
                    "topic": topic.name,
                    "students_affected": student_count,
                    "percentage": avg_score_rounded,
                    "level": proficiency_level,
                    "stage": topic_stage,
                }
            )

        # Apply filters
        filtered_data = performance_data

        if stage:
            filtered_data = [item for item in filtered_data if item["stage"] == stage]

        if level:
            filtered_data = [item for item in filtered_data if item["level"] == level]

        return filtered_data

    def get_student_dashboard_overview(
        self, student_id, subject_id=None, batch_id=None
    ):
        """
        total_tests: int
        current_streak: int
        highest_streak: int
        total_achievements: int
        """
        tests = test_manager.get_tests_by_student_ids([student_id])
        student = student_manager.get_student_by_id(student_id)
        achievements = student_has_achievement_manager.get_student_achievements_number(
            student_id
        )
        return {
            "total_tests": len(tests),
            "current_streak": student.current_streak,
            "highest_streak": student.highest_streak,
            "total_achievements": achievements,
        }

    def get_student_practice_overview(self, student_id, subject_id=None, batch_id=None):
        from app.analytics.operations import sts_manager

        # 1) Load and filter topics by subject (if provided)
        student_topic_scores = sts_manager.select_student_topic_score_history(
            student_id
        )
        topics = topic_manager.get_topic_by_ids(
            [s.topic_id for s in student_topic_scores]
        )
        if subject_id:
            topics = [t for t in topics if getattr(t, "subject_id", None) == subject_id]
        topics_by_id = {t.id: t for t in topics}

        if not topics_by_id:
            return {
                "mastery_percent": 0.0,
                "mastery_stage": self.get_performance_band(0.0),
                "topics": [],
                "mastery_zone": [],
                "power_up_zone": [],
            }

        # 2) Aggregate scores per topic
        sums, counts = defaultdict(float), defaultdict(int)
        for s in student_topic_scores:
            if s.topic_id in topics_by_id:
                sums[s.topic_id] += float(s.score_acquired)
                counts[s.topic_id] += 1

        if not sums:
            return {
                "mastery_percent": 0.0,
                "mastery_stage": self.get_performance_band(0.0),
                "topics": [],
                "mastery_zone": [],
                "power_up_zone": [],
            }

        # 3) Compute per-topic averages
        topic_avg = {tid: (sums[tid] / counts[tid]) for tid in sums.keys()}

        # 4) Build topic mastery items
        topic_mastery_items = []
        for tid, avg in topic_avg.items():
            band = self.get_performance_band(avg)
            topic_mastery_items.append(
                {
                    "topic_id": tid,
                    "topic_name": topics_by_id[tid].name,
                    "avg_score": round(avg, 2),
                    "mastery_level": band,
                }
            )

        # Sort topics by score descending for main list
        topic_mastery_items.sort(key=lambda x: x["avg_score"], reverse=True)

        # 5) Identify zones
        # Power-up zone → 2 lowest scoring topics
        power_up_zone = sorted(topic_mastery_items, key=lambda x: x["avg_score"])[:2]

        # Mastery zone → 2 best topics excluding those already in power_up_zone
        power_up_ids = {t["topic_id"] for t in power_up_zone}
        mastery_zone = [
            t for t in topic_mastery_items if t["topic_id"] not in power_up_ids
        ][:2]

        # 6) Compute overall mastery
        overall_avg = round(sum(topic_avg.values()) / len(topic_avg), 2)

        return {
            "mastery_percent": overall_avg,
            "mastery_stage": self.get_performance_band(overall_avg),
            "topics": topic_mastery_items,
            "mastery_zone": mastery_zone,
            "power_up_zone": power_up_zone,
        }

    def get_student_weekly_goals(self, student_id):
        """
        Get all weekly goals for a student with their current progress.
        Returns a list of goal items with subject names and progress percentages.
        """
        from datetime import timedelta
        from app.goals.models import WeeklyGoal
        from app.app_admin.operations import subject_manager

        goals = (
            WeeklyGoal.query.filter_by(student_id=student_id, is_active=True)
            .order_by(WeeklyGoal.week_start_date.desc())
            .all()
        )

        # Get all subject IDs
        subject_ids = [g.subject_id for g in goals if g.subject_id is not None]
        subjects_dict = {}
        if subject_ids:
            subjects = subject_manager.get_subjects_by_ids(list(set(subject_ids)))
            subjects_dict = {s.id: s.name for s in subjects}

        goals_data = []
        for goal in goals:
            progress_percent = (
                (goal.current_value / goal.target_value * 100)
                if goal.target_value > 0
                else 0
            )

            goals_data.append(
                {
                    "goal_id": goal.id,
                    "subject_id": goal.subject_id,
                    "subject_name": (
                        subjects_dict.get(goal.subject_id) if goal.subject_id else None
                    ),
                    "week_start_date": str(goal.week_start_date),
                    "week_end_date": str(goal.week_start_date + timedelta(days=6)),
                    "status": goal.status.value,
                    "target_metric": goal.target_metric.value,
                    "target_value": goal.target_value,
                    "current_value": goal.current_value,
                    "progress_percent": round(progress_percent, 2),
                    "achieved_at": goal.achieved_at,
                }
            )

        return goals_data

    def get_student_weekly_wins_messages(self, student_id):
        """
        Generate weekly wins messages for achieved goals using the message generator.
        Returns a list of messages with goal information.
        """
        from app.goals.models import WeeklyGoal, GoalStatus
        from app.app_admin.operations import subject_manager
        from app.analytics.weekly_messages_generator import (
            GoalMessageGenerator,
            GoalMetric as MsgGoalMetric,
        )

        # Get achieved goals (only achieved status)
        achieved_goals = (
            WeeklyGoal.query.filter_by(
                student_id=student_id, status=GoalStatus.achieved
            )
            .order_by(WeeklyGoal.achieved_at.desc())
            .all()
        )

        if not achieved_goals:
            return []

        # Get subject names
        subject_ids = [g.subject_id for g in achieved_goals if g.subject_id is not None]
        subjects_dict = {}
        if subject_ids:
            subjects = subject_manager.get_subjects_by_ids(list(set(subject_ids)))
            subjects_dict = {s.id: s.name for s in subjects}

        messages = []
        for goal in achieved_goals:
            subject_name = (
                subjects_dict.get(goal.subject_id) if goal.subject_id else None
            )

            # Map goal metric to message generator metric
            if goal.target_metric.value == "xp":
                metric = MsgGoalMetric.xp
            elif goal.target_metric.value == "streak_days":
                metric = MsgGoalMetric.streak_days
            else:
                metric = MsgGoalMetric.xp  # default

            # Generate achievement message
            message = GoalMessageGenerator.achievement(
                metric=metric,
                subject=subject_name,
                value=goal.current_value,
                target=goal.target_value,
                progress=goal.current_value,
            )

            messages.append(
                {
                    "message": message,
                    "goal_id": goal.id,
                    "subject_name": subject_name,
                    "metric": goal.target_metric.value,
                    "variant": "success",
                    "icon": "trophy",
                }
            )

        return messages

    def get_student_achievements(
        self, student_id: int, include_requirements: bool = False
    ) -> List[Dict[str, Any]]:
        """Return a student's achievements with metadata and counts."""
        from app.achievements.models import StudentHasAchievement, Achievement
        from app.extensions import db

        rows = (
            db.session.query(StudentHasAchievement, Achievement)
            .join(Achievement, Achievement.id == StudentHasAchievement.achievement_id)
            .filter(StudentHasAchievement.student_id == student_id)
            .all()
        )

        results: List[Dict[str, Any]] = []
        for sha, ach in rows:
            item = ach.to_json(
                include_requirements=include_requirements
            )  # id, name, description, image_url, class[, requirements]
            # Ensure stable keys expected by callers
            item.update(
                {
                    "achievement_id": ach.id,  # redundant with "id", but convenient
                    "number_of_times": sha.number_of_times or 1,
                    "first_awarded_at": (
                        sha.created_at.isoformat()
                        if getattr(sha, "created_at", None)
                        else None
                    ),
                    "last_awarded_at": (
                        getattr(sha, "updated_at", None).isoformat()
                        if getattr(sha, "updated_at", None)
                        else None
                    ),
                }
            )
            results.append(item)

        # Sort newest awards first (fallback to first_awarded)
        results.sort(
            key=lambda x: x.get("last_awarded_at") or x.get("first_awarded_at") or "",
            reverse=True,
        )
        return results


analytics_service = AnalyticsService()
