import calendar
from datetime import datetime, timezone
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Any, Optional, Iterable

import json

from apiflask.exceptions import HTTPError

from app.student.operations import student_manager, batch_manager
from app.test.operations import test_manager, question_manager
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

    recommendation_level = {
        "highly": "High Recommendation",
        "moderately": "Moderate Recommendation",
        "lowly": "Low Recommendation",
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
        self, school_id: str, batch_id: str, time_range: str, subject_id: str = None
    ) -> Dict[str, Any]:
        """
        Calculates student practice rates and distributions.
        time_range options: 'week', 'month', 'all_time'
        """
        # 1. Fetch data from backend
        this_tests, last_tests, all_student_ids = self.configure_performance_requirements(
            school_id, batch_id, time_range, subject_id
        )

        total_students = len(all_student_ids)
        if total_students == 0:
            return self._get_empty_state()

        # 2. Define Dynamic Thresholds (min_tests, max_tests)
        # Standards adjusted for 2025 learning engagement benchmarks
        if time_range == "this_week":
            thresholds = {"minimal": (1, 1), "consistent": (2, 4), "high": (5, 10**6)}
        elif time_range == "this_month":
            thresholds = {"minimal": (1, 4), "consistent": (5, 12), "high": (13, 10**6)}
        else:  # all_time
            thresholds = {"minimal": (1, 10), "consistent": (11, 30), "high": (31, 10**6)}

        # 3. Current Period Calculation
        students_practiced_this_period = set(t.student_id for t in this_tests)
        practiced_number = len(students_practiced_this_period)
        practiced_percent = round((practiced_number / total_students) * 100, 2)
        
        tests_per_student = round(len(this_tests) / total_students, 2)

        # 4. Comparison Logic (Excluded for 'all_time')
        comparison = None
        change_from = 0.0
        change_direction = "same"

        if time_range != "all_time":
            students_practiced_last_period = set(t.student_id for t in last_tests)
            current_rate = practiced_number / total_students
            previous_rate = len(students_practiced_last_period) / total_students if total_students > 0 else 0.0

            if previous_rate > 0:
                # Relative % change between the two periods
                comparison = round(((current_rate - previous_rate) / previous_rate) * 100, 2)
                change_from = round(previous_rate * 100, 2)
                if comparison > 0.1: # 0.1% buffer for stability
                    change_direction = "up"
                elif comparison < -0.1:
                    change_direction = "down"
            elif current_rate > 0:
                change_direction = "up"

        # 5. Tier Distribution
        test_counts = Counter(t.student_id for t in this_tests)

        def get_tier_stats(min_t: int, max_t: int) -> Dict[str, Any]:
            count = sum(1 for c in test_counts.values() if min_t <= c <= max_t)
            return {
                "number": count,
                "percent": round((count / total_students) * 100, 2)
            }

        tier_distribution = {
            "no_practice": {
                "number": total_students - practiced_number,
                "percent": round(100 - practiced_percent, 2),
            },
            "minimal_practice": get_tier_stats(*thresholds["minimal"]),
            "consistent_practice": get_tier_stats(*thresholds["consistent"]),
            "high_practice": get_tier_stats(*thresholds["high"]),
        }

        return {
            "number_of_tests_per_student": tests_per_student,
            "change_from": change_from,
            "change_direction": change_direction,
            "comparison": comparison,
            "practiced_number": practiced_number,
            "practiced_percent": practiced_percent,
            "not_practiced_number": total_students - practiced_number,
            "not_practiced_percent": round(100 - practiced_percent, 2),
            "tier_distribution": tier_distribution,
            "total_students": total_students,
            "time_range": time_range
        }

    def _get_empty_state(self) -> Dict[str, Any]:
        return {
            "number_of_tests_per_student": 0,
            "comparison": None,
            "change_from": 0,
            "change_direction": "same",
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
            "total_students": 0,
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
                (abs(test.finished_on - test.started_on)).total_seconds() for test in tests
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

        tests_info = []

        for test in sorted_tests:
            tests_info.append(
                {
                    "description": f"{student_dict[test.student_id].first_name} completed a test in {subject_dict[test.subject_id].short_name} and scored {test.score_acquired}%",
                    "time": test.finished_on,
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
                    round(band_counts["highly_proficient"] / total_students, 2) * 100
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "proficient",
                "students": band_counts["proficient"],
                "percentage": (
                    round(band_counts["proficient"] / total_students, 2) * 100
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "approaching_proficient",
                "students": band_counts["approaching"],
                "percentage": (
                    round(band_counts["approaching"] / total_students, 2) * 100
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "developing",
                "students": band_counts["developing"],
                "percentage": (
                    round(band_counts["developing"] / total_students, 2) * 100
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "emerging",
                "students": band_counts["emerging"],
                "percentage": (
                    round(band_counts["emerging"] / total_students, 2) * 100
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

        total_students = len(set(student_ids))

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

    def _get_weighted_preparedness_for_subject(self, student_id: int, subject_id: int) -> float:
        """
        Compute coverage-weighted preparedness for a student in a subject.

        Formula: Σ(question_count_for_topic × student_avg_score) / Σ(question_count_for_topic)

        Unattempted topics contribute 0 to the numerator but are still in the denominator,
        so a student who has only covered a fraction of the curriculum scores proportionally lower.
        Topics with no active questions are excluded entirely.
        """
        topics = topic_manager.get_topic_by_subject(subject_id)
        if not topics:
            return 0.0

        question_counts = question_manager.get_question_counts_by_subject(subject_id)

        averages_rows = sts_manager.get_averages_for_topics_by_subject_id(student_id, subject_id)
        student_averages = {row.topic_id: float(row.average_score) for row in averages_rows}

        total_weight = 0.0
        weighted_score_sum = 0.0

        for topic in topics:
            weight = question_counts.get(topic.id, 0)
            if weight == 0:
                continue
            score = student_averages.get(topic.id, 0.0)
            weighted_score_sum += weight * score
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_score_sum / total_weight, 2)

    def get_performance_indicators(self, student_id, subject_id=None, batch_id=None):
        student = student_manager.get_student_by_id(student_id)
        tests = test_manager.get_tests_by_student_ids([student_id])
        if subject_id:
            tests = [test for test in tests if test.subject_id == subject_id]

        if subject_id:
            average_score = self._get_weighted_preparedness_for_subject(student_id, subject_id)
        else:
            subjects = subject_manager.get_subject_by_curriculum("bece")
            subject_scores = [
                self._get_weighted_preparedness_for_subject(student_id, s.id)
                for s in subjects
            ]
            average_score = round(sum(subject_scores) / len(subject_scores), 2) if subject_scores else 0.0

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
        subjects = subject_manager.get_subject_by_curriculum("bece")
        if subject_id:
            subjects = [s for s in subjects if s.id == subject_id]

        subject_performance = []

        for subject in subjects:
            average_score = self._get_weighted_preparedness_for_subject(student_id, subject.id)
            proficiency = self.get_performance_band(average_score)

            subject_performance.append(
                {
                    "subject_id": subject.id,
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
        added_topic_ids = set()

        failing_topics = []
        for recommendation in recommendations:
            if ( recommendation.topic_id in added_topic_ids):
                continue

            topic_scores = sts_manager.select_student_topic_score_history(student_id, recommendation.topic_id)
            failing_topics.append(
                {
                    "topic_name": topics[recommendation.topic_id].name,
                    "subject_name": subjects[
                        topics[recommendation.topic_id].subject_id
                    ].name,
                    "average_score": round(
                        (
                            sum(test.score_acquired for test in topic_scores) / len(topic_scores)
                            if len(topic_scores) > 0
                            else 0
                        ), 2),
                    "proficiency": self.recommendation_level[recommendation.recommendation_level],
                }
            )
            added_topic_ids.add(recommendation.topic_id)

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

    def get_performance_topics(self, subject_id, batch_id=None, stage=None, level=None, threshold=50):
        """
        Get performance data for topics with details of struggling students.

        Args:
            subject_id: The subject to analyze
            batch_id (str, optional): Filter by specific batch
            stage (str, optional): Filter by stage (e.g., "Stage 1-3", "Stage 4-6", "Stage 7-9")
            level (str, optional): Filter by proficiency level (e.g., "EMERGING", "DEVELOPING", "APPROACHING_PROFICIENT", "PROFICIENT", "HIGHLY_PROFICIENT")
            threshold (int, optional): Score below which students are considered struggling (default: 50)

        Returns:
            list: Topic performance data with struggling student details, sorted by number of struggling students (descending)
        """
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

        # Get all individual scores (not aggregated)
        all_scores = query.all()

        # Get topics for this subject to map topic_id to topic details
        topics = topic_manager.get_topic_by_subject(subject_id)
        topic_dict = {topic.id: topic for topic in topics}

        # Group scores by topic and student (to calculate averages per student per topic)
        topic_data = {}
        for score_record in all_scores:
            topic_id = score_record.topic_id
            student_id = score_record.student_id
            
            if topic_id not in topic_dict:
                continue
                
            if topic_id not in topic_data:
                topic_data[topic_id] = {
                    'student_scores': {}  # student_id -> list of scores
                }
            
            # Group scores by student for this topic
            if student_id not in topic_data[topic_id]['student_scores']:
                topic_data[topic_id]['student_scores'][student_id] = []
            
            topic_data[topic_id]['student_scores'][student_id].append(score_record.score_acquired)

        # Build performance data
        performance_data = []
        for topic_id, data in topic_data.items():
            topic = topic_dict[topic_id]
            
            # Calculate per-student averages and build student list
            student_averages = []
            all_student_avg_scores = []
            
            for student_id, scores in data['student_scores'].items():
                # Calculate average score for this student in this topic
                student_avg = sum(scores) / len(scores) if scores else 0
                all_student_avg_scores.append(student_avg)
                
                # Fetch student details
                student = student_manager.get_student_by_id(student_id)
                
                # Construct student name
                if student:
                    student_name = f"{student.first_name} {student.surname}"
                else:
                    student_name = f"Student {student_id}"
                
                student_averages.append({
                    'id': student_id,
                    'name': student_name,
                    'score': round(student_avg, 2),
                    'proficiency_level': self.get_performance_band(student_avg).upper()
                })
            
            # Calculate overall topic average from student averages
            avg_score = sum(all_student_avg_scores) / len(all_student_avg_scores) if all_student_avg_scores else 0
            avg_score_rounded = round(avg_score, 2)
            
            # Get overall proficiency level
            proficiency_level = self.get_performance_band(avg_score_rounded).upper()
            
            # Get stage
            topic_stage = get_stage_from_level(topic.level)
            
            # Filter struggling students (average score below threshold)
            struggling_students = [
                student for student in student_averages 
                if student['score'] < threshold
            ]
            
            performance_data.append({
                "topic": topic.name,
                "topic_id": topic_id,
                "total_students": len(student_averages),
                "students_affected": len(struggling_students),  # Only struggling students
                "percentage": avg_score_rounded,
                "level": proficiency_level,
                "stage": topic_stage,
                "struggling_students": struggling_students
            })

        # Apply filters
        filtered_data = performance_data

        if stage:
            filtered_data = [item for item in filtered_data if item["stage"] == stage]

        if level:
            filtered_data = [item for item in filtered_data if item["level"] == level]

        # Sort by number of struggling students (highest first - most urgent)
        filtered_data.sort(key=lambda x: x['students_affected'], reverse=True)

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

        # 5) Identify zones using percentage-based thresholds
        # Mastery zone → topics with 85%+ (mastered)
        # Power-up zone → topics with < 85% (needs work)
        # Ensure no overlap: a topic cannot be in both zones
        
        mastery_zone = [
            t for t in topic_mastery_items if t["avg_score"] >= 80
        ]
        
        power_up_zone = [
            t for t in topic_mastery_items if t["avg_score"] < 60
        ]
        
        # Sort mastery zone by score (best first), take top 2
        mastery_zone.sort(key=lambda x: x["avg_score"], reverse=True)
        mastery_zone = mastery_zone[:2]
        
        # Sort power-up zone by score (lowest first), take bottom 2
        power_up_zone.sort(key=lambda x: x["avg_score"])
        power_up_zone = power_up_zone[:2]

        # 6) Compute overall mastery using coverage-weighted formula across all subject topics
        if subject_id:
            overall_avg = self._get_weighted_preparedness_for_subject(student_id, subject_id)
        else:
            subjects = subject_manager.get_subject_by_curriculum("bece")
            subject_scores = [
                self._get_weighted_preparedness_for_subject(student_id, s.id)
                for s in subjects
            ]
            overall_avg = round(sum(subject_scores) / len(subject_scores), 2) if subject_scores else 0.0

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

    def _ach_progress_percent(self, ach, student, tests, max_level) -> float:
        """Compute progress (0–100) for one locked achievement using pre-loaded data.

        Callers are responsible for short-circuiting earned achievements (progress = 100).
        """
        if not ach.requirements:
            return 0.0
        try:
            requirements = json.loads(ach.requirements)
        except Exception:
            return 0.0
        if not requirements:
            return 0.0

        ach_class = ach.achievement_class

        if ach_class == "volume_practice":
            target = int(requirements.get("number_of_tests") or 0)
            if target <= 0:
                return 0.0
            return round((min(len(tests), target) / target) * 100.0, 2)

        if ach_class == "continuous_practice":
            target = int(requirements.get("streak_days") or 0)
            if target <= 0:
                return 0.0
            current = min(int(student.current_streak or 0), target)
            return round((current / target) * 100.0, 2)

        if ach_class == "level_ups":
            target = int(requirements.get("level") or 0)
            if target <= 0:
                return 0.0
            return round((min(max_level, target) / target) * 100.0, 2)

        if ach_class == "mastery_level":
            score_min = float(requirements.get("score_band_min") or 0)
            score_max = float(requirements.get("score_band_max") or 0)
            target = int(requirements.get("number_of_tests") or 0)
            if target <= 0:
                return 0.0
            within = sum(1 for t in tests if score_min <= float(t.score_acquired) <= score_max)
            return round((min(within, target) / target) * 100.0, 2)

        if ach_class == "speed_and_accuracy":
            expected_q = requirements.get("questions_count")
            if expected_q is None:
                return 0.0

            candidates = []
            for t in tests:
                tmeta = t.meta or {}
                tq = (tmeta.get("total_questions") if isinstance(tmeta, dict) else None) or t.question_number
                if tq is None:
                    continue
                if int(tq) == int(expected_q):
                    candidates.append(t)
            if not candidates:
                return 0.0

            metric = requirements.get("metric")
            requires_finish = bool(requirements.get("requires_finish_before_time_end"))

            best = 0.0
            for t in candidates:
                tmeta = t.meta or {}
                out_time = (tmeta.get("out_time") or 0) if isinstance(tmeta, dict) else 0
                if requires_finish and not (out_time and int(out_time) > 0):
                    continue

                if metric == "score_percent":
                    score_min = float(requirements.get("score_min") or 0)
                    score_max = float(requirements.get("score_max") or 100)
                    pct = 100.0 if (score_min <= float(t.score_acquired) <= score_max) else 0.0
                    best = max(best, pct)
                    continue

                if metric == "mistakes_count":
                    max_mistakes = int(requirements.get("max_mistakes") or 0)
                    mistakes = tmeta.get("mistakes_count") if isinstance(tmeta, dict) else None
                    if mistakes is None:
                        continue

                    mistakes = int(mistakes)
                    if mistakes <= max_mistakes:
                        best = max(best, 100.0)
                    else:
                        extra = mistakes - max_mistakes
                        best = max(best, 50.0 if extra == 1 else 0.0)
                    continue

            return best

        return 0.0

    def get_student_achievements(
        self, student_id: int, include_requirements: bool = False
    ) -> List[Dict[str, Any]]:
        """Return ALL achievements (earned and locked) with progress percentages."""
        from app.achievements.models import StudentHasAchievement, Achievement
        from app.student.models import StudentSubjectLevel
        from app.extensions import db

        all_achievements = Achievement.query.filter_by(is_deleted=False).all()
        if not all_achievements:
            return []

        earned_rows = (
            db.session.query(StudentHasAchievement)
            .filter(StudentHasAchievement.student_id == student_id)
            .all()
        )
        earned_map = {sha.achievement_id: sha for sha in earned_rows}

        # Pre-load per-student data once so progress for N locked achievements
        # doesn't fan out into 3N queries.
        needs_progress = any(ach.id not in earned_map for ach in all_achievements)
        student = student_manager.get_student_by_id(student_id) if needs_progress else None
        if student:
            tests = test_manager.get_tests_by_student_ids([student_id])
            levels = StudentSubjectLevel.query.filter_by(student_id=student_id).all()
            max_level = max((lvl.level for lvl in levels), default=0)
        else:
            tests, max_level = [], 0

        results: List[Dict[str, Any]] = []
        for ach in all_achievements:
            item = ach.to_json(include_requirements=include_requirements)
            sha = earned_map.get(ach.id)
            is_earned = sha is not None

            if is_earned:
                progress_percentage = 100.0
            elif student is not None:
                progress_percentage = self._ach_progress_percent(ach, student, tests, max_level)
            else:
                progress_percentage = 0.0

            item.update({
                "id": ach.id,
                "achievement_id": ach.id,
                "is_earned": is_earned,
                "progress_percentage": progress_percentage,
                "number_of_times": sha.number_of_times if sha else 0,
                "first_awarded_at": (
                    sha.created_at.isoformat()
                    if sha and getattr(sha, "created_at", None)
                    else None
                ),
                "last_awarded_at": (
                    sha.updated_at.isoformat()
                    if sha and getattr(sha, "updated_at", None)
                    else (sha.created_at.isoformat() if sha and getattr(sha, "created_at", None) else None)
                ),
            })
            results.append(item)

        results.sort(
            key=lambda x: (
                not x["is_earned"],
                -x["progress_percentage"],
                x.get("last_awarded_at") or x.get("first_awarded_at") or "",
            )
        )
        return results
    
    def _batch_snapshot(self, batch_id):
        """Compute headline metrics for a single batch."""
        batch = batch_manager.get_batch_by_id(batch_id)
        if not batch:
            return None
        students = batch.to_json(include_students=True, include_subjects=False, include_staff=False)["students"]
        student_ids = [s["id"] for s in students]

        if not student_ids:
            return {
                "batch_id": batch.id,
                "batch_name": batch.batch_name,
                "status": batch.status or "active",
                "academic_year": batch.academic_year,
                "exam_year": batch.exam_year,
                "total_students": 0,
                "average_score": 0.0,
                "total_tests": 0,
                "tier_distribution": {
                    "highly_proficient": {"count": 0, "percentage": 0.0},
                    "proficient": {"count": 0, "percentage": 0.0},
                    "approaching_proficient": {"count": 0, "percentage": 0.0},
                    "developing": {"count": 0, "percentage": 0.0},
                    "emerging": {"count": 0, "percentage": 0.0},
                },
            }

        tests = test_manager.get_tests_by_student_ids(student_ids)
        total_students = len(student_ids)
        avg = (sum(t.score_acquired for t in tests) / len(tests)) if tests else 0.0

        tiers = {
            band: self.calculate_student_average_performance(total_students, tests, band)
            for band in self.performance_bands.keys()
        }

        return {
            "batch_id": batch.id,
            "batch_name": batch.batch_name,
            "status": batch.status or "active",
            "academic_year": batch.academic_year,
            "exam_year": batch.exam_year,
            "total_students": total_students,
            "average_score": round(avg, 2),
            "total_tests": len(tests),
            "tier_distribution": tiers,
        }

    def compare_batches(self, batch_ids, school_id=None):
        """Return side-by-side batch snapshots + a delta summary.

        school_id, if provided, scopes access — any batch not in that school is dropped.
        """
        snapshots = []
        for bid in batch_ids:
            snap = self._batch_snapshot(bid)
            if not snap:
                continue
            if school_id is not None:
                batch = batch_manager.get_batch_by_id(bid)
                if batch and batch.school_id != school_id:
                    continue
            snapshots.append(snap)

        delta = None
        if len(snapshots) == 2:
            diff = round(snapshots[1]["average_score"] - snapshots[0]["average_score"], 2)
            if diff > 0.5:
                summary = f"Year-over-year improvement: +{diff}pp average score"
            elif diff < -0.5:
                summary = f"Decline: {diff}pp average score"
            else:
                summary = "Flat"
            delta = {
                "average_score_delta": diff,
                "tests_delta": snapshots[1]["total_tests"] - snapshots[0]["total_tests"],
                "students_delta": snapshots[1]["total_students"] - snapshots[0]["total_students"],
                "summary": summary,
            }

        return {
            "batches": snapshots,
            "delta": delta,
        }

    # Recommendation pruning rules:
    #   - Mastery (priority): topics now scoring >= MASTERY_THRESHOLD are dropped immediately.
    #   - Age: source recommendations older than REC_MAX_AGE_DAYS are dropped (mastery still wins).
    #   - Hard cap of REC_MAX_ITEMS so the teacher card stays scannable.
    MASTERY_THRESHOLD = 80
    REC_MAX_AGE_DAYS = 14
    REC_MAX_ITEMS = 3

    def get_recommendations(self, student_id, subject_id=None):
        """Heuristic recommendations for teachers based on failing topics + recent practice gaps.

        Pruned by current mastery (highest priority) and source-recommendation age.
        Capped at REC_MAX_ITEMS to keep the teacher-facing card scannable.
        """
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        age_cutoff = now - timedelta(days=self.REC_MAX_AGE_DAYS)

        raw_recs = ssr_manager.select_student_recommendations(student_id)
        topic_ids = list({r.topic_id for r in raw_recs})
        topics_by_id = {t.id: t for t in topic_manager.get_topic_by_ids(topic_ids)} if topic_ids else {}
        subject_ids = list({t.subject_id for t in topics_by_id.values()})
        subjects_by_id = {s.id: s for s in subject_manager.get_subjects_by_ids(subject_ids)} if subject_ids else {}

        # Pre-aggregate topic averages in one shot to avoid N queries inside the loop
        all_scores = sts_manager.select_student_topic_score_history(student_id)
        score_sum = defaultdict(float)
        score_count = defaultdict(int)
        for s in all_scores:
            score_sum[s.topic_id] += float(s.score_acquired)
            score_count[s.topic_id] += 1
        topic_avg_by_id = {
            tid: round(score_sum[tid] / score_count[tid], 2)
            for tid in score_count
        }

        # Pick the most-recent source rec per topic so age check uses latest data
        latest_by_topic = {}
        for r in raw_recs:
            existing = latest_by_topic.get(r.topic_id)
            if existing is None or (r.created_at and existing.created_at and r.created_at > existing.created_at):
                latest_by_topic[r.topic_id] = r

        recs = []
        for topic_id, rec_row in latest_by_topic.items():
            topic = topics_by_id.get(topic_id)
            if not topic:
                continue
            if subject_id and topic.subject_id != subject_id:
                continue

            # Mastery prune (priority): if topic avg has reached mastery, drop the rec
            avg_score = topic_avg_by_id.get(topic_id)
            if avg_score is None:
                continue
            if avg_score >= self.MASTERY_THRESHOLD:
                continue

            # Age prune: drop recommendations whose source row is older than the cutoff
            rec_created = rec_row.created_at
            if rec_created and rec_created.tzinfo is None:
                rec_created = rec_created.replace(tzinfo=timezone.utc)
            if rec_created and rec_created < age_cutoff:
                continue

            priority = "high" if avg_score < 50 else ("medium" if avg_score < 65 else "low")
            subject = subjects_by_id.get(topic.subject_id)
            recs.append({
                "id": f"failing-{topic_id}",
                "title": f"Drill {topic.name}",
                "body": (
                    f"This student's average in this topic is {avg_score}%. "
                    "Targeted practice on a few questions per day will lift this faster than mixed-subject tests."
                ),
                "subject_name": subject.name if subject else None,
                "topic_name": topic.name,
                "priority": priority,
                "_sort_score": avg_score,
            })

        # Lowest scores first, then cap
        recs.sort(key=lambda r: r["_sort_score"])
        recs = recs[: self.REC_MAX_ITEMS]
        for r in recs:
            r.pop("_sort_score", None)

        # If there's still room, surface a streak nudge (informational, never blocks a topic rec)
        if len(recs) < self.REC_MAX_ITEMS:
            student = student_manager.get_student_by_id(student_id)
            if student and (student.current_streak or 0) >= 3:
                recs.append({
                    "id": "streak-keep-alive",
                    "title": "Keep the streak going",
                    "body": (
                        f"This student is on a {student.current_streak}-day streak. "
                        "A short test today protects it — worth a nudge."
                    ),
                    "subject_name": None,
                    "topic_name": None,
                    "priority": "low",
                })

        return {
            "recommendations": recs[: self.REC_MAX_ITEMS],
            "generated_at": now.isoformat(),
        }

    # region Deep Dive: time per question / best topics / integrity

    def _question_correctness_and_time(self, test):
        """Yield (topic_id, time_seconds, is_correct) tuples per main question in a graded test.

        Sub-questions are not surfaced individually — they contribute to scoring but
        don't carry a per-question timing signal from the client.
        """
        questions = test.questions or []
        for q in questions:
            if not isinstance(q, dict):
                continue
            meta = q.get("meta") or {}
            time_ms = meta.get("time_spent")
            if time_ms is None:
                continue
            try:
                time_seconds = float(time_ms) / 1000.0
            except (TypeError, ValueError):
                continue
            if time_seconds <= 0:
                continue
            topic_id = q.get("topic_id")
            student_answer = q.get("student_answer")
            correct_answer = q.get("correct_answer")
            if correct_answer is None or student_answer is None:
                continue
            is_correct = student_answer == correct_answer
            yield topic_id, time_seconds, is_correct

    def get_time_per_question(self, student_id, subject_id=None, batch_id=None):
        """Per-topic median splits each question into Fast vs Slow; correctness gives 4 buckets.

        Per-topic median means a 'slow' question in fractions isn't the same threshold as
        a 'slow' question in essays — topics with naturally longer questions are handled fairly.
        """
        tests = test_manager.get_tests_by_student_ids([student_id])
        if subject_id:
            tests = [t for t in tests if t.subject_id == subject_id]

        topic_times = defaultdict(list)
        records = []
        for test in tests:
            for topic_id, time_seconds, is_correct in self._question_correctness_and_time(test):
                if topic_id is None:
                    continue
                topic_times[topic_id].append(time_seconds)
                records.append((topic_id, time_seconds, is_correct))

        if not records:
            def _empty():
                return {"count": 0, "avg_seconds": 0.0}
            return {
                "avg_seconds": 0.0,
                "total_questions": 0,
                "fast_correct": _empty(),
                "fast_wrong": _empty(),
                "slow_correct": _empty(),
                "slow_wrong": _empty(),
            }

        # Per-topic median; needs ≥2 samples for the split to be meaningful, otherwise
        # we treat the question as fast (it has no peer to compare against).
        topic_medians = {}
        for topic_id, times in topic_times.items():
            if len(times) < 2:
                topic_medians[topic_id] = None
                continue
            sorted_times = sorted(times)
            mid = len(sorted_times) // 2
            if len(sorted_times) % 2 == 0:
                topic_medians[topic_id] = (sorted_times[mid - 1] + sorted_times[mid]) / 2.0
            else:
                topic_medians[topic_id] = sorted_times[mid]

        buckets = {
            "fast_correct": [],
            "fast_wrong": [],
            "slow_correct": [],
            "slow_wrong": [],
        }
        for topic_id, time_seconds, is_correct in records:
            median = topic_medians.get(topic_id)
            is_slow = median is not None and time_seconds > median
            key = (
                ("slow_correct" if is_correct else "slow_wrong")
                if is_slow
                else ("fast_correct" if is_correct else "fast_wrong")
            )
            buckets[key].append(time_seconds)

        def _summarize(values):
            if not values:
                return {"count": 0, "avg_seconds": 0.0}
            return {"count": len(values), "avg_seconds": round(sum(values) / len(values), 2)}

        all_times = [t for _, t, _ in records]
        return {
            "avg_seconds": round(sum(all_times) / len(all_times), 2),
            "total_questions": len(all_times),
            "fast_correct": _summarize(buckets["fast_correct"]),
            "fast_wrong": _summarize(buckets["fast_wrong"]),
            "slow_correct": _summarize(buckets["slow_correct"]),
            "slow_wrong": _summarize(buckets["slow_wrong"]),
        }

    BEST_TOPICS_MIN_SCORE = 70
    BEST_TOPICS_LIMIT = 5

    def get_best_topics(self, student_id, subject_id=None, batch_id=None):
        """Mirror of failing topics for the high end of the distribution."""
        scores = sts_manager.select_student_topic_score_history(student_id)
        if not scores:
            return []

        topic_ids = list({s.topic_id for s in scores})
        topics_by_id = {t.id: t for t in topic_manager.get_topic_by_ids(topic_ids)}
        if subject_id:
            topics_by_id = {tid: t for tid, t in topics_by_id.items() if t.subject_id == subject_id}

        topic_scores = defaultdict(list)
        for s in scores:
            if s.topic_id in topics_by_id:
                topic_scores[s.topic_id].append(float(s.score_acquired))

        results = []
        for topic_id, vals in topic_scores.items():
            avg = round(sum(vals) / len(vals), 2)
            if avg < self.BEST_TOPICS_MIN_SCORE:
                continue
            results.append({
                "topic_name": topics_by_id[topic_id].name,
                "average_score": avg,
                "proficiency": self.get_performance_band(avg),
            })

        results.sort(key=lambda r: r["average_score"], reverse=True)
        return results[: self.BEST_TOPICS_LIMIT]

    INTEGRITY_OUT_TIME_THRESHOLD_MS = 10000
    INTEGRITY_WINDOW_SIZE = 15
    INTEGRITY_FLAG_THRESHOLD = 5

    def _extract_outside_time_ms(self, meta):
        """Pull the cumulative-outside-time signal from test meta.

        The frontend originally sent `out_time`; the mark_test handler now normalizes
        it to `outside_time_ms`, but older rows may still carry the legacy key.
        """
        if not isinstance(meta, dict):
            return 0
        for key in ("outside_time_ms", "out_time"):
            value = meta.get(key)
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        return 0

    def get_integrity_summary(self, student_id, subject_id=None, batch_id=None):
        """Rolling-window flag: last N tests in the subject; if M+ have cumulative
        out-of-fullscreen time over the threshold, surface a teacher note.

        Returns the count, threshold, window size, and the flagged tests themselves so
        the teacher can investigate rather than just see a number.
        """
        tests = test_manager.get_tests_by_student_ids([student_id])
        if subject_id:
            tests = [t for t in tests if t.subject_id == subject_id]

        # Only completed tests count — in-progress submissions would skew the window
        tests = [t for t in tests if t.is_completed and t.created_at is not None]
        tests.sort(key=lambda t: t.created_at, reverse=True)
        window = tests[: self.INTEGRITY_WINDOW_SIZE]

        flagged = []
        for t in window:
            out_ms = self._extract_outside_time_ms(t.meta)
            if out_ms >= self.INTEGRITY_OUT_TIME_THRESHOLD_MS:
                meta = t.meta or {}
                flagged.append({
                    "test_id": t.id,
                    "date": (t.created_at.isoformat() if t.created_at else None),
                    "out_time_ms": out_ms,
                    "outside_events": int(meta.get("outside_events") or 0) if isinstance(meta, dict) else 0,
                    "max_outside_event_ms": int(meta.get("max_outside_event_ms") or 0) if isinstance(meta, dict) else 0,
                })

        subject_name = None
        if subject_id:
            subj = subject_manager.get_subject_by_id(subject_id)
            if subj:
                subject_name = subj.name

        return {
            "suspect_test_count": len(flagged),
            "window_size": self.INTEGRITY_WINDOW_SIZE,
            "threshold": self.INTEGRITY_FLAG_THRESHOLD,
            "subject_name": subject_name,
            "flagged_tests": flagged,
        }

    # endregion Deep Dive


    def get_overall_preparedness(self, student_id, subject_id=None, batch_id=None):
        """
        Get overall preparedness data for a student including average mastery and subject-wise performance.
        """
        subject_performance = self.get_subject_proficiency(student_id, subject_id, batch_id)
        
        if not subject_performance:
            average_mastery = 0.0
        else:
            average_mastery = round(
                sum(subj["average_score"] for subj in subject_performance) / len(subject_performance), 2
            )
        
        return {
            "average_mastery": average_mastery,
            "subjects": subject_performance
        }


analytics_service = AnalyticsService()
