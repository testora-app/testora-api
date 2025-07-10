from app.test.models import Question, SubQuestion, Test, QuestionImage
from app._shared.operations import BaseManager
import json

from typing import List, Dict, Union
from sqlalchemy.sql import func


# region Question Manager
class QuestionManager(BaseManager):

    def get_questions(self) -> List[Question]:
        return Question.query.filter_by(is_deleted=False).all()

    def get_questions_by_topics(self, topic_ids: List[int]):
        return Question.query.filter(Question.topic_id.in_(topic_ids)).all()

    def get_question_by_id(self, question_id) -> Question:
        return Question.query.filter_by(id=question_id).first()

    def get_question_by_ids(self, question_ids) -> List[Question]:
        return Question.query.filter(Question.id.in_(question_ids)).all()

    def get_subquestion_by_parent(self, question_id) -> List[SubQuestion]:
        return SubQuestion.query.filter_by(parent_question_id=question_id).all()

    def create_subquestion(
        self,
        parent_question_id,
        text,
        correct_answer,
        possible_answers,
        points,
        is_save_function=True,
        **kwargs
    ):
        new_sub = SubQuestion(
            parent_question_id=parent_question_id,
            text=text,
            correct_answer=correct_answer,
            possible_answers=str(possible_answers),
            points=points,
            **kwargs
        )

        if is_save_function:
            self.save(new_sub)

        return new_sub

    def create_question(
        self,
        text,
        correct_answer,
        possible_answers,
        topic_id,
        points,
        school_id=None,
        is_save_function=True,
        **kwargs
    ) -> Question:
        new_question = Question(
            text=text,
            correct_answer=correct_answer,
            possible_answers=str(possible_answers),
            topic_id=topic_id,
            points=points,
            school_id=school_id,
            **kwargs
        )

        if is_save_function:
            self.save(new_question)

        return new_question

    def save_multiple_questions(self, questions: List[Dict]) -> List[Question]:
        questions_list: List[Question] = []
        sub_questions_list = []
        for obj in questions:
            sub_obj = obj.pop("sub_questions", [])
            answer_images = obj.pop("answer_images", [])
            question_images = obj.pop("question_images", [])

            new_question = self.create_question(**obj, is_save_function=True)
            questions_list.append(new_question)

            if sub_obj:
                for sub in sub_obj:
                    new_sub = self.create_subquestion(
                        parent_question_id=new_question.id,
                        **sub,
                        is_save_function=True
                    )
                    sub_questions_list.append(new_sub)

            if question_images + answer_images:
                for image in question_images + answer_images:
                    self.create_question_image(
                        question_id=new_question.id,
                        **image
                    )


        # self.save_multiple(questions_list)
        # self.save_multiple(sub_questions_list)

        return self.get_question_by_ids(question.id for question in questions_list)

    def get_sub_question_by_id(self, sub_id) -> SubQuestion:
        return SubQuestion.query.filter_by(id=sub_id).first()

    def create_question_image(self, question_id, image_url, label=None, is_for_answer=False):
        new_image = QuestionImage(
            question_id=question_id,
            image_url=image_url,
            label=label,
            is_for_answer=is_for_answer,
        )
        self.save(new_image)
        return new_image


# endregion Question Manager


# region TestManager
class TestManager(BaseManager):

    def get_tests(self):
        return Test.query.order_by(Test.created_at.desc()).all()

    def get_test_by_id(self, test_id) -> Union[Test, None]:
        return Test.query.filter_by(id=test_id).first()

    def get_tests_by_school_id(self, school_id) -> List[Test]:
        return (
            Test.query.filter_by(school_id=school_id, is_completed=True)
            .order_by(Test.created_at.desc())
            .all()
        )

    def get_tests_by_student_ids(
        self, student_ids: List[int], subject_id=None
    ) -> List[Test]:
        if subject_id:
            return (
                Test.query.filter(
                    Test.student_id.in_(student_ids),
                    Test.is_completed == True,
                    Test.subject_id == subject_id,
                    Test.is_deleted == False
                )
                .order_by(Test.created_at.desc())
                .all()
            )
        return (
            Test.query.filter(
                Test.student_id.in_(student_ids), Test.is_completed == True, Test.is_deleted == False
            )
            .order_by(Test.created_at.desc())
            .all()
        )

    def get_last_test_by_student_id(self, student_id, subject_id) -> Test:
        return (
            Test.query.filter_by(
                student_id=student_id,
                subject_id=subject_id,
                is_deleted=False,
                is_completed=True,
            )
            .order_by(Test.finished_on.desc())
            .first()
        )

    def get_tests_by_subject_and_student(self, student_id, subject_id) -> List[Test]:
        return (
            Test.query.filter_by(
                student_id=student_id, subject_id=subject_id, is_completed=True
            )
            .order_by(Test.created_at.desc())
            .all()
        )

    def get_student_recent_tests(
        self, student_id, subject_id=None, limit=6
    ) -> List[Test]:
        q = Test.query.filter_by(student_id=student_id, is_completed=True)
        if subject_id:
            q = q.filter_by(subject_id=subject_id)

        return q.order_by(Test.created_at.desc()).limit(limit).all()

    def get_average_test_scores(self, student_ids=None) -> List[Dict]:
        return (
            Test.query.filter(Test.is_completed == True)  # Filter for completed tests
            .with_entities(
                Test.subject_id,
                func.avg(Test.score_acquired).label(
                    "average_score"
                ),  # Calculate average score
            )
            .group_by(Test.subject_id)  # Group by subject_id
            .filter(Test.student_id.in_(student_ids))
            .all()
        )

    def create_test(
        self,
        student_id,
        subject_id,
        questions,
        total_points,
        question_number,
        school_id,
        total_score=100,
        points_acquired=0,
        score_acquired=0,
        started_on=None,
        finished_on=None,
        questions_correct=None,
        meta=None,
        is_completed=False,
    ):
        new_test = Test(
            student_id=student_id,
            subject_id=subject_id,
            questions=questions,
            total_points=total_points,
            total_score=total_score,
            question_number=question_number,
            school_id=school_id,
            points_acquired=points_acquired,
            score_acquired=score_acquired,
            started_on=started_on,
            finished_on=finished_on,
            questions_correct=questions_correct,
            meta=meta,
            is_completed=is_completed,
        )

        self.save(new_test)
        return new_test


# endregion TestManager


class QuestionImageManager(BaseManager):
    def create_question_image(self, question_id, image_url, label=None, is_for_answer=False):
        new_image = QuestionImage(
            question_id=question_id,
            image_url=image_url,
            label=label,
            is_for_answer=is_for_answer,
        )
        self.save(new_image)
        return new_image

question_manager = QuestionManager()
test_manager = TestManager()
