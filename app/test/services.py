import random
from collections import defaultdict

from app._shared.schemas import ExamModes, QuestionsNumberLimiter, QuestionPoints
from app.test.operations import question_manager
from app.admin.models import Topic
from app.extensions import db
from app.test.models import Question

from typing import List

class TestService:

    @staticmethod
    def is_mode_accessible(exam_mode, student_level):
        # the exam_mode and the level that it is accessible at
        levels = {
            ExamModes.level: 0,
            ExamModes.exam: 6
        }
        # if the student level is greater than or equal to the desired exam mode, allow them else nooo!
        return student_level >= levels[exam_mode]
    
    @classmethod
    def __generate_level_counts(cls, total_questions, max_level):
        levels = list(range(1, max_level + 1))
        level_counts = defaultdict(int)

        remaining_questions = total_questions
        while remaining_questions > 0:
            level = random.choice(levels)
            level_counts[level] += 1
            remaining_questions -= 1

        return dict(level_counts)
    

    @staticmethod
    def determine_total_test_points(questions) -> int:
        # question level times it's points multiplier
        question_multiplier = QuestionPoints.get_question_level_points()

        total_points = 0

        for question in questions:
            number_of_sub = len(question['sub_questions'])
            total_points += (question['level'] + number_of_sub) * question_multiplier[question['level']]

        return round(total_points, 2)
    

    @staticmethod
    def determine_question_points(question, main_correct=True, sub_questions_correct=0) -> int:
        question_multiplier = QuestionPoints.get_question_level_points()

        if main_correct:
            return (question['level'] + sub_questions_correct)  * question_multiplier[question['level']]
        return sub_questions_correct * question['level']

    #NOTE: this already takes up sub questions
    @staticmethod
    def generate_random_questions_by_level(subject_id, student_level) -> List[Question]:
        total_questions = QuestionsNumberLimiter.get_question_limit_for_level(student_level)
        level_counts = TestService.__generate_level_counts(total_questions, student_level) # max level is student_level

        questions = []
        
        for level, count in level_counts.items():
            level_questions = (
                db.session.query(Question)
                .join(Topic, Question.topic_id == Topic.id)
                .filter(Topic.level == level, Topic.subject_id == subject_id)
                .order_by(db.func.random())
                .limit(count)
                .all()
            )
            questions.extend(level_questions)
        
        # Shuffle the final list to ensure overall randomness
        random.shuffle(questions)
        return questions
    
    @staticmethod
    def mark_test(questions, deduct_points=False):
        # we need a way to determine if we're deducting points lost or half points

        points_acquired = 0
        score_acquired = 0

        for question in questions:
            # get the question
            q = question_manager.get_question_by_id(question['id'])
            main_question_correct = False
            no_subs_correct = 0
            if q.correct_answer == question['student_answer']:
                main_question_correct = True
                score_acquired += 1
            else:
                if deduct_points:
                    points_acquired -= TestService.determine_question_points(question)


            # mark sub questions if any
            if len(question['sub_questions']) > 0:
                for sub in question['sub_questions']:
                    s = question_manager.get_sub_question_by_id(sub['id'])
                    if s.correct_answer == s['student_answer']:
                        no_subs_correct += 1
                    else:
                        if deduct_points:
                            points_acquired -= 1


            points = round(TestService.determine_question_points(question, main_correct=main_question_correct, \
                                                                 sub_questions_correct=no_subs_correct), 2)
            points_acquired += points
            question['correct_answer'] = q.correct_answer
            question['points'] = points

        return {
            'questions': questions,
            'points_acquired': round(points_acquired, 2),
            'score_acquired': score_acquired
        }
            
            
'''
    
def get_weighted_random_questions(n, subject_id, max_level):
    random_questions = (
        db.session.query(Question)
        .join(Topic, Question.topic_id == Topic.id)
        .filter(Topic.subject_id == subject_id, Topic.level <= max_level)
        .order_by(db.func.random() * Topic.level.desc())
        .limit(n)
        .all()
    )
    return random_questions

'''



