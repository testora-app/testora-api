from flask import render_template
from app.student.models import (
    Student,
    Batch,
    StudentSubjectLevel,
    StudentLevellingHistory,
)
from app._shared.operations import BaseManager
from app._shared.services import hash_password

from typing import List, Union


class StudentManager(BaseManager):
    def create_student(
        self,
        first_name,
        surname,
        email,
        password,
        school_id,
        is_approved=False,
        is_archived=False,
        other_names=None,
    ) -> Student:
        new_student = Student(
            first_name=first_name,
            surname=surname,
            email=email,
            password_hash=hash_password(password),
            school_id=school_id,
            is_approved=is_approved,
            other_names=other_names,
            is_archived=is_archived,
        )

        self.save(new_student)
        return new_student

    def get_student_by_id(self, student_id) -> Student:
        return Student.query.get(student_id)

    def get_student_by_email(self, email) -> Student:
        return Student.query.filter_by(email=email).first()

    def get_student(self) -> List[Student]:
        return Student.query.all()

    def get_student_by_school(self, school_id) -> List[Student]:
        return Student.query.filter_by(school_id=school_id, is_deleted=False).all()

    def get_active_students_by_school(self, school_id) -> List[Student]:
        return Student.query.filter_by(
            school_id=school_id, is_deleted=False, is_approved=True, is_archived=False
        ).all()

    @staticmethod
    def get_students_by_ids(student_ids) -> List[Student]:
        return Student.query.filter(Student.id.in_(student_ids)).all()

    def update_streak(self, student_id, current_login_time):
        student: Student = Student.query.get(student_id)
        title = ""
        content = ""
        streak_modified = False
        if student and student.last_login:
            # Calculate the difference in days between the current login and the last login
            days_difference = (
                current_login_time.date() - student.last_login.date()
            ).days

            if days_difference == 1:
                # Logged in on the next day
                student.current_streak += 1
                student.highest_streak = max(
                    student.current_streak, student.highest_streak
                )

                title = "Streak Increased"
                content = f"Great job! Your login streak is now {student.current_streak} days."
                streak_modified = True
            else:
                # More than one day has passed, or same day login, reset streak
                student.current_streak = 1
                title = "Streak Reset"
                content = "Your login streak has been reset. Start a new streak today!"
                streak_modified = True
        else:
            # First time login
            student.current_streak = 1
            student.highest_streak = 1

        student.last_login = current_login_time
        student.save()

        return {
            "message": {
                "title": title,
                "content": content
            },
            "streak_modified": streak_modified
        }



class BatchManager(BaseManager):
    def create_batch(self, batch_name, school_id, curriculum, students=[]):
        new_batch = Batch(
            batch_name=batch_name, school_id=school_id, curriculum=curriculum
        )

        self.save(new_batch)

        students = StudentManager.get_students_by_ids(students)

        for student in students:
            new_batch.students.append(student)

        new_batch.save()
        return new_batch

    def get_all_batches(self) -> List[Batch]:
        return Batch.query.all()

    def get_batch_by_id(self, batch_id) -> Batch:
        return Batch.query.get(batch_id)

    def get_batches_by_school_id(self, school_id) -> List[Batch]:
        return Batch.query.filter_by(school_id=school_id).all()

    def get_batch_by_curriculum(self, curriculum) -> List[Batch]:
        return Batch.query.filter_by(curriculum=curriculum).all()


class StudentSubjectLevelManager(BaseManager):
    def get_student_subject_level(
        self, student_id, subject_id=None
    ) -> Union[List[StudentSubjectLevel], StudentSubjectLevel]:
        if subject_id:
            return StudentSubjectLevel.query.filter_by(
                student_id=student_id, subject_id=subject_id
            ).first()
        return StudentSubjectLevel.query.filter_by(student_id=student_id).all()

    def init_student_subject_level(self, student_id, subject_id) -> StudentSubjectLevel:
        new_level = StudentSubjectLevel(
            student_id=student_id, subject_id=subject_id, level=1, points=0
        )
        self.save(new_level)
        return new_level


class LevelHistoryManager(BaseManager):
    def get_levelling_history(
        self, student_id, subject_id=None
    ) -> List[StudentLevellingHistory]:
        if subject_id:
            return StudentLevellingHistory.query.filter_by(
                student_id=student_id, subject_id=subject_id
            ).all()
        return StudentLevellingHistory.query.filter_by(student_id=student_id).all()

    def add_new_history(self, student_id, subject_id, level_from, level_to):
        new_history = StudentLevellingHistory(
            student_id=student_id,
            subject_id=subject_id,
            level_from=level_from,
            level_to=level_to,
        )

        self.save(new_history)
        return new_history


student_manager = StudentManager()
batch_manager = BatchManager()
stusublvl_manager = StudentSubjectLevelManager()
level_history_manager = LevelHistoryManager()
