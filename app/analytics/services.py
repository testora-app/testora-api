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

        return this_tests, last_tests, all_student_ids

    def get_practice_rate(self, school_id, batch_id, time_range, subject_id=None):
        this_tests, last_tests, all_student_ids = (
            self.configure_performance_requirements(
                school_id, batch_id, time_range, subject_id
            )
        )

        # Tier Distributions
        these_students_took_tests_this_param = set(
            [test.student_id for test in this_tests]
        )
        these_students_took_tests_last_param = set(
            [test.student_id for test in last_tests]
        )

        number_of_test_per_student = len(this_tests) / len(all_student_ids)
        comparison = (
            (
                len(these_students_took_tests_this_param)
                - len(these_students_took_tests_last_param)
            )
            / len(these_students_took_tests_last_param)
            if len(these_students_took_tests_last_param) > 0
            else 0
        )

        practiced_percent = len(these_students_took_tests_this_param) / len(
            all_student_ids
        )
        practiced_number = len(these_students_took_tests_this_param)

        not_practiced_percent = 100 - practiced_percent
        not_practiced_number = len(all_student_ids) - practiced_number

        minimal_practice_number, minimal_practice_percent = self.count_in_range(
            this_tests, 1, 2
        )
        consistent_practice_number, consistent_practice_percent = self.count_in_range(
            this_tests, 3, 5
        )
        high_practice_number, high_practice_percent = self.count_in_range(
            this_tests, 6, 1000
        )

        tier_distribution = {
            "no_practice": {
                "number": not_practiced_number,
                "percent": not_practiced_percent,
            },
            "minimal_practice": {
                "number": minimal_practice_number,
                "percent": minimal_practice_percent,
            },
            "consistent_practice": {
                "number": consistent_practice_number,
                "percent": consistent_practice_percent,
            },
            "high_practice": {
                "number": high_practice_number,
                "percent": high_practice_percent,
            },
        }

        return {
            "rate": number_of_test_per_student,
            "unit": "tests/student",
            "change_from": comparison,
            "change_direction": "up" if comparison > 0 else "down",
            "total_students": len(all_student_ids),
            "practiced_percent": practiced_percent,
            "practiced_number": practiced_number,
            "not_practiced_percent": not_practiced_percent,
            "not_practiced_number": not_practiced_number,
            "tier_distribution": tier_distribution,
        }

    def calculate_student_average_performance(
        self, total_number_of_students, tests, performance_band
    ):
        """
        Calculates the average performance of students in a given performance band
        So if the performance_band is "highly_proficient", it will calculate the average performance of students who are highly proficient
        Args:
          total_number_of_students (int): The total number of students
          tests (list): The list of tests
          performance_band (str): The performance band
        Returns:
          - the number of students in that band
          - the percentage of students in that band
        """
        filtered_tests = [
            test
            for test in tests
            if self.get_performance_band(test.score_acquired) == performance_band
        ]
        number_of_students_in_band = len(
            set([test.student_id for test in filtered_tests])
        )
        percentage_of_students_in_band = (
            number_of_students_in_band / total_number_of_students
        )

        return {
            "count": number_of_students_in_band,
            "percentage": percentage_of_students_in_band,
        }

    def get_performance_distribution(
        self, school_id, batch_id, time_range, subject_id=None
    ):
        this_tests, last_tests, all_student_ids = (
            self.configure_performance_requirements(
                school_id, batch_id, time_range, subject_id
            )
        )

        if time_range == "this_week":
            tests = this_tests
        elif time_range == "last_week":
            tests = last_tests
        else:
            tests = this_tests + last_tests

        if subject_id:
            subject = subject_manager.get_subject_by_id(subject_id)
            subject_name = subject.name
        else:
            subject_name = "Overall"

        average_score = round(
            sum(test.score_acquired for test in tests) / len(tests)
            if len(tests) > 0
            else 0
        )

        proficiency_percent = average_score
        proficiency_status = self.get_performance_band(average_score)

        total_students = len(all_student_ids)

        tier_distribution = {
            "highly_proficient": self.calculate_student_average_performance(
                total_students, tests, "highly_proficient"
            ),
            "proficient": self.calculate_student_average_performance(
                total_students, tests, "proficient"
            ),
            "approaching": self.calculate_student_average_performance(
                total_students, tests, "approaching"
            ),
            "emerging": self.calculate_student_average_performance(
                total_students, tests, "emerging"
            ),
            "developing": self.calculate_student_average_performance(
                total_students, tests, "developing"
            ),
        }

        proficiency_above = (
            tier_distribution["highly_proficient"]["count"]
            + tier_distribution["proficient"]["count"]
        )
        proficiency_above_percent = (
            proficiency_above / total_students if total_students > 0 else 0
        )
        at_risk = (
            tier_distribution["approaching"]["count"]
            + tier_distribution["emerging"]["count"]
            + tier_distribution["developing"]["count"]
        )
        at_risk_percent = at_risk / total_students if total_students > 0 else 0

        summary_distribution = {
            "proficiency_above": {
                "count": proficiency_above,
                "percentage": round(proficiency_above_percent, 2),
            },
            "at_risk": {"count": at_risk, "percentage": round(at_risk_percent, 2)},
            "average_tests": {"value": len(tests), "unit": "/week"},
            "average_time_spent": {
                "value": round(
                    (
                        sum(
                            (test.finished_on.minute - test.started_on.minute)
                            for test in tests
                        )
                        / len(tests)
                        if len(tests) > 0
                        else 0
                    ),
                    2,
                ),
                "unit": "min/student",
            },
        }

        return {
            "subject_name": subject_name,
            "proficiency_percent": round(proficiency_percent, 2),
            "proficiency_status": proficiency_status,
            "tier_distribution": tier_distribution,
            "summary_distribution": summary_distribution,
            "last_updated": self.most_recent_created_at(tests),
        }

    def get_subject_performance(self, school_id, batch_id, subject_id=None):
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

        subjects = subject_manager.get_subject_by_curriculum("bece")

        subject_distribution = []

        for subject in subjects:
            students_with_highly_proficient = len(
                set([
                    test.student_id
                    for test in tests
                    if test.subject_id == subject.id
                    and self.get_performance_band(test.score_acquired)
                    == "highly_proficient"
                ])
            )
            students_with_proficient = len(
                set([
                    test.student_id
                    for test in tests
                    if test.subject_id == subject.id
                    and self.get_performance_band(test.score_acquired) == "proficient"
                ])
            )

            student_readiness_number = (
                students_with_highly_proficient + students_with_proficient
            )
            student_readiness_percent = (
                student_readiness_number / len(student_ids) * 100
            )

            number_of_subject_tests = len(
                [test for test in tests if test.subject_id == subject.id]
            )
            average_subject_score = (
                sum(
                    test.score_acquired
                    for test in tests
                    if test.subject_id == subject.id
                )
                / number_of_subject_tests
                if number_of_subject_tests > 0
                else 0
            )

            subject_distribution.append(
                {
                    "subject_name": subject.name,
                    "student_readiness_number": student_readiness_number,
                    "student_readiness_percent": student_readiness_percent,
                    "status": self.get_performance_band(average_subject_score),
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
                "name": "Highly Proficient",
                "students": band_counts["highly_proficient"],
                "percentage": (
                    band_counts["highly_proficient"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "Proficient",
                "students": band_counts["proficient"],
                "percentage": (
                    band_counts["proficient"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "Approaching",
                "students": band_counts["approaching"],
                "percentage": (
                    band_counts["approaching"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "Developing",
                "students": band_counts["developing"],
                "percentage": (
                    band_counts["developing"] / total_students
                    if total_students > 0
                    else 0
                ),
            },
            {
                "name": "Emerging",
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
        student_topic_scores = sts_manager.select_student_topic_score_history(student_id)
        topics = topic_manager.get_topic_by_ids([topic_id for topic_id in student_topic_scores])

        topics = {topic.id: topic for topic in topics}

        topic_bands = {}
        for score in student_topic_scores:
            proficiency_band = self.get_performance_band(score.score_acquired)
            if proficiency_band not in topic_bands:
                topic_bands[proficiency_band] = {'count': 0, 'topics': []}
            
            topic_bands[proficiency_band]['count'] += 1
            topic_bands[proficiency_band]['topics'].append(topics[score.topic_id].name)

        
        proficiency_graph = []
        for band, data in topic_bands.items():
            proficiency_graph.append({
                'band': band,
                'count': data['count'],
                'topics': data['topics']
            })
            
        return proficiency_graph

    def get_failing_topics(self, student_id, subject_id=None, batch_id=None):
        recommendations = ssr_manager.select_student_recommendations(student_id)
        topics = topic_manager.get_topic_by_ids([topic_id for topic_id in recommendations])

        topics = {topic.id: topic for topic in topics}

        failing_topics = []
        for recommendation in recommendations:
            failing_topics.append({
                'topic_name': topics[recommendation.topic_id].name,
                'average_score': 0, #TODO: calculate average score
                'proficiency': recommendation.recommendation_level
            })
            
        return failing_topics

analytics_service = AnalyticsService()
