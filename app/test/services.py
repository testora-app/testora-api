import random
from collections import defaultdict

from app._shared.schemas import ExamModes, QuestionsNumberLimiter, QuestionPoints
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
    def __generate_level_counts(total_questions, max_level):
        levels = list(range(1, max_level + 1))
        level_counts = defaultdict(int)

        remaining_questions = total_questions
        while remaining_questions > 0:
            level = random.choice(levels)
            level_counts[level] += 1
            remaining_questions -= 1

        return dict(level_counts)
    

    @staticmethod
    def determine_toal_test_points(questions) -> int:
        # question level times it's points multiplier
        question_multiplier = QuestionPoints.get_question_level_points()

        total_points = 0

        for question in questions:
            total_points += question['level'] * question_multiplier[question['level']]
        return total_points
    

    #TODO: modify this to take into consideration subquestions, and the subquestions should not be
    # randomized from their main question (just store them as single questions chale lmao)
    # or think about it well
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



