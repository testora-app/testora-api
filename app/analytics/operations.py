from app._shared.operations import BaseManager
from app.analytics.models import StudentTopicScores
from typing import  List, Dict


class StudentTopicScoresManager(BaseManager):

    def select_student_topic_score_history(self, student_id, topic_id=None)-> List[StudentTopicScores]:
        if topic_id:
            return StudentTopicScores.query.filter_by(student_id=student_id, topic_id=topic_id).all()
        return StudentTopicScores.query.filter_by(student_id=student_id).all()
    
    def insert_student_topic_score(self, student_id, subject_id, test_id, topic_id, score_acquired) -> StudentTopicScores:
        new_score = StudentTopicScores(
            student_id=student_id,
            subject_id=subject_id,
            test_id=test_id,
            topic_id=topic_id,
            score_acquired=score_acquired
        )

        self.save(new_score)
        return new_score
    
    def insert_multiple_student_topic_scores(self, entities: List[Dict]):
        to_save: List[StudentTopicScores] = []
        for entity in entities:
            to_save.append(
                StudentTopicScores(
                    student_id=entity['student_id'],
                    subject_id=['subject_id'],
                    test_id=['test_id'],
                    topic_id=['topic_id'],
                    score_acquired=['score_acquired']
                )
            )
        self.save_multiple(to_save)
        return [entity.to_json() for entity in to_save]
    


sts_manager = StudentTopicScoresManager()