from datetime import datetime, timezone
from collections import Counter
from typing import List, Dict, Tuple, Any, Optional, Iterable

from app.student.operations import student_manager, batch_manager
from app.test.operations import test_manager
from app.app_admin.operations import subject_manager

class AnalyticsService:

    performance_bands = {
        "highly_proficient": 80,
        "proficient": 70,
        "approaching_proficient": 65,
        "developing": 50,
        "emerging": 0
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

    def most_recent_created_at(self, items: Iterable[Any], key: str = "created_at") -> Optional[datetime]:
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
        for band, threshold in sorted(self.performance_bands.items(),
                                      key=lambda kv: kv[1], reverse=True):
            if score >= threshold:
                return band
        return "emerging"

    def get_time_range(self, time_range):
        if time_range == "this_week":
            return datetime.now(timezone.utc).isocalendar().week, datetime.now(timezone.utc).isocalendar().year
        elif time_range == "this_month":
            return datetime.now(timezone.utc).month, datetime.now(timezone.utc).year
        elif time_range == "all_time":
            return None, None


    def get_last_time_range(self, time_range):
        if time_range == "this_week":
            return datetime.now(timezone.utc).isocalendar().week - 1, datetime.now(timezone.utc).isocalendar().year
        elif time_range == "this_month":
            return datetime.now(timezone.utc).month - 1, datetime.now(timezone.utc).year
        elif time_range == "all_time":
            return None, None

    
    def count_in_range(self, records: List[Dict[str, Any]], min_times: int, max_times: int, id_key: str = "student_id") -> Tuple[int, float]:
        """
        Returns:
          - number of objects whose student_id appears between [min_times, max_times] (inclusive)
          - percentage of such objects out of all objects (0–100)
        """
        if not records:
            return 0, 0.0
        if min_times > max_times:
            min_times, max_times = max_times, min_times

        counts = Counter(r.get(id_key) for r in records if id_key in r)
        qualifying_ids = {sid for sid, c in counts.items() if min_times <= c <= max_times}

        qualifying_objects = sum(1 for r in records if r.get(id_key) in qualifying_ids)
        pct = qualifying_objects * 100.0 / len(records)
        return qualifying_objects, round(pct, 2)


    
    def configure_performance_requirements(self, school_id, batch_id, time_range, subject_id=None):
        week, year = self.get_time_range(time_range)
        last_week, last_year = self.get_last_time_range(time_range)

        all_students = student_manager.get_active_students_by_school(school_id)
        all_student_ids = [student.id for student in all_students]

        # get the batch in question
        if batch_id:
            batch = batch_manager.get_batch_by_id(batch_id)
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
            this_tests = [test for test in this_tests if test.created_at.isocalendar().week == week and test.created_at.isocalendar().year == year]
        elif week and year and time_range == "this_month":
            this_tests = [test for test in this_tests if test.created_at.month == week and test.created_at.year == year]
        else:
            this_tests = this_tests

        
        # now get the last week or month
        if last_week and last_year and time_range == "this_week":
            last_tests = [test for test in this_tests if test.created_at.isocalendar().week == last_week and test.created_at.isocalendar().year == last_year]
        elif last_week and last_year and time_range == "this_month":
            last_tests = [test for test in this_tests if test.created_at.month == last_week and test.created_at.year == last_year]
        else:
            last_tests = this_tests
    

        if subject_id:
            last_tests = [test for test in last_tests if test.subject_id == subject_id]

        return this_tests, last_tests, all_student_ids


    def get_practice_rate(self, school_id, batch_id, time_range, subject_id=None):
        this_tests, last_tests, all_student_ids = self.configure_performance_requirements(school_id, batch_id, time_range, subject_id)
        

        # Tier Distributions
        these_students_took_tests_this_param = set([test.student_id for test in this_tests])
        these_students_took_tests_last_param = set([test.student_id for test in last_tests])
        
        number_of_test_per_student = len(this_tests) / len(all_student_ids)
        comparison = (len(these_students_took_tests_this_param) - len(these_students_took_tests_last_param)) / len(these_students_took_tests_last_param)

        practiced_percent = len(these_students_took_tests_this_param) / len(all_student_ids)
        practiced_number = len(these_students_took_tests_this_param)

        not_practiced_percent = 1 - practiced_percent
        not_practiced_number = len(all_student_ids) - practiced_number

        minimal_practice_number, minimal_practice_percent = self.count_in_range(this_tests, 1, 2)
        consistent_practice_number, consistent_practice_percent = self.count_in_range(this_tests, 3, 5)
        high_practice_number, high_practice_percent = self.count_in_range(this_tests, 6, 1000)


        tier_distribution = {
            "no_practice": {
                "number": not_practiced_number,
                "percent": not_practiced_percent
            },
            "minimal_practice": {
                "number": minimal_practice_number,
                "percent": minimal_practice_percent
            },
            "consistent_practice": {
                "number": consistent_practice_number,
                "percent": consistent_practice_percent
            },
            "high_practice": {
                "number": high_practice_number,
                "percent": high_practice_percent
            }
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
            "tier_distribution": tier_distribution
        }

    
    def calculate_student_average_performance(self, total_number_of_students, tests, performance_band):
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
        filtered_tests = [test for test in tests if self.get_performance_band(test.score_acquired) == performance_band]
        number_of_students_in_band = len(set([test.student_id for test in filtered_tests]))
        percentage_of_students_in_band = number_of_students_in_band / total_number_of_students

        return {
            "count": number_of_students_in_band,
            "percentage": percentage_of_students_in_band
        }


    def get_performance_distribution(self, school_id, batch_id, time_range, subject_id=None):
        this_tests, last_tests, all_student_ids = self.configure_performance_requirements(school_id, batch_id, time_range, subject_id)

        if time_range == "this_week":
            tests = this_tests
        elif time_range == "last_week":
            tests = last_tests
        
        if subject_id:
            subject = subject_manager.get_subject_by_id(subject_id)
            subject_name = subject.name
        else:
            subject_name = "Overall"

        
        average_score = sum(test.score_acquired for test in tests) / len(tests)

        proficiency_percent = average_score
        proficiency_status = self.get_performance_band(average_score)

        total_students = len(all_student_ids)


        tier_distribution = {
            "highly_proficient": self.calculate_student_average_performance(total_students, tests, "highly_proficient"),
            "proficient": self.calculate_student_average_performance(total_students, tests, "proficient"),
            "approaching": self.calculate_student_average_performance(total_students, tests, "approaching"),
            "emerging": self.calculate_student_average_performance(total_students, tests, "emerging"),
            "developing": self.calculate_student_average_performance(total_students, tests, "developing")
        }

        proficiency_above = tier_distribution["highly_proficient"]["count"] + tier_distribution["proficient"]["count"]
        proficiency_above_percent = proficiency_above / total_students
        at_risk = tier_distribution["approaching"]["count"] + tier_distribution["emerging"]["count"] + tier_distribution["developing"]["count"]
        at_risk_percent = at_risk / total_students

        summary_distribution = {
            "proficiency_above": {
                "count": proficiency_above,
                "percentage": proficiency_above_percent
            },
            "at_risk": {
                "count": at_risk,
                "percentage": at_risk_percent
            },
            "average_tests": {
                "value": len(tests),
                "unit": "/week"
            },
            "average_time_spent": {
                "value": sum((test.finished_on.minute - test.started_on.minute) for test in tests) / len(tests),
                "unit": "min/student"
            }
        }


        return {
            "subject_name": subject_name,
            "proficiency_percent": proficiency_percent,
            "proficiency_status": proficiency_status,
            "tier_distribution": tier_distribution,
            "summary_distribution": summary_distribution,
            "last_updated": self.most_recent_created_at(tests)
        }

        

        

            




analytics_service = AnalyticsService()