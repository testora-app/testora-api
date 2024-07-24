from app.test.models import Question, SubQuestion, Test
from app._shared.operations import BaseManager
import json

from typing import List, Dict, Union


#region Question Manager
class QuestionManager(BaseManager):

    def get_questions(self) -> List[Question]:
        return Question.query.all()
    
    def get_questions_by_topics(self, topic_ids: List[int]):
        return Question.query.filter(Question.topic_id.in_(topic_ids)).all()
    
    def get_question_by_id(self, question_id) -> Question:
        return Question.query.filter_by(id=question_id).first()
    
    def get_question_by_ids(self, question_ids) -> Question:
        return Question.query.filter(Question.id.in_(question_ids)).all()
    
    def get_subquestion_by_parent(self, question_id) -> List[SubQuestion]:
        return Question.query.filter_by(parent_question_id=question_id).all()
    
    def create_subquestion(self, parent_question_id, text, correct_answer, possible_answers, points, is_save_function=True):
        new_sub = SubQuestion(
            parent_question_id=parent_question_id,
            text=text,
            correct_answer=correct_answer,
            possible_answers=str(possible_answers),
            points=points
        )

        if is_save_function:
            self.save(new_sub)

        return new_sub
    
    def create_question(self, text, correct_answer, possible_answers, topic_id, points, school_id=None, is_save_function=True) -> Question:
        new_question = Question(
            text=text,
            correct_answer=correct_answer,
            possible_answers=str(possible_answers),
            topic_id=topic_id,
            points=points,
            school_id=school_id
        )

        if is_save_function:
            self.save(new_question)

        return new_question
    
    def save_multiple_questions(self, questions: List[Dict]) -> List[Question]:
        questions_list : List[Question] = []
        sub_questions_list = []
        for obj in questions:
            sub_obj = obj.get('sub_questions', [])
            new_question = self.create_question(**obj, is_save_function=False)
            questions_list.append(new_question)
            for sub in sub_obj:
                new_sub = self.create_subquestion(parent_question_id=new_question.id, **sub, is_save_function=False)
                sub_questions_list.append(new_sub)

        self.save_multiple(questions_list)
        self.save_multiple(sub_questions_list)


        return self.get_question_by_ids(question.id for question in questions_list)
    

    def get_sub_question_by_id(self, sub_id) -> SubQuestion:
        return SubQuestion.query.filter_by(id=sub_id).first() 
    
#endregion Question Manager


#region TestManager
class TestManager(BaseManager):
    
    def get_tests(self):
        return Test.query.all()
    
    def get_test_by_id(self, test_id) -> Union[Test, None]:
        return Test.query.filter_by(id=test_id).first()
    
    def get_tests_by_school_id(self, school_id) -> List[Test]:
        return Test.query.filter_by(school_id=school_id).all()
    
    def get_tests_by_student_ids(self, student_ids:List[int]) -> List[Test]:
        return Test.query.filter(Test.student_id.in_(student_ids), Test.is_completed == True).all()
    
    def create_test(self, student_id, subject_id, questions, total_points, total_score, question_number, school_id,
                    points_acquired=0, score_acquired=0, started_on=None, finished_on=None,
                    questions_correct=None, meta=None, is_completed=False):
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
            is_completed=is_completed
        )

        self.save(new_test)
        return new_test
    

#endregion TestManager



question_manager = QuestionManager()
test_manager = TestManager()