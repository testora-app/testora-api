from app._shared.operations import BaseManager
from app.analytics.models import StudentTopicScores, StudentBestSubject, StudentSubjectRecommendation
from sqlalchemy import func
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
                    **entity
                )
            )
        self.save_multiple(to_save)
        return [entity.to_json() for entity in to_save]
    
    def get_averages_for_topics_by_subject_id(self, student_id, subject_id) -> List[StudentTopicScores]:
        return \
            StudentTopicScores.query.with_entities(
                StudentTopicScores.topic_id,
                func.avg(StudentTopicScores.score_acquired).label('average_score')
            )\
            .filter_by(student_id=student_id, subject_id=subject_id)\
            .group_by(StudentTopicScores.topic_id)
        
    

class StudentBestSubjectManager(BaseManager):
    def select_student_best(self, student_id, subject_id=None, include_archived=False) -> List[StudentBestSubject]:
        if subject_id:
            return StudentBestSubject.query.filter_by(student_id=student_id, subject_id=subject_id, is_archived=include_archived).all()
        return StudentBestSubject.query.filter_by(student_id=student_id, subject_id=subject_id, is_archived=include_archived).all()
    
    def insert_student_best(self, student_id, subject_id, topic_id, proficiency_level) -> StudentBestSubject:
        new_best = StudentBestSubject(
            student_id=student_id,
            subject_id=subject_id,
            topic_id=topic_id,
            proficiency_level=proficiency_level
        )
        self.save(new_best)
        return new_best

    def insert_multiple_bests(self, entities: List[Dict]):
        to_save: List[StudentBestSubject] = []
        for entity in entities:
            to_save.append(
                StudentBestSubject(**entity)
            )
        self.save_multiple(to_save)
        return [entity.to_json() for entity in to_save]
    
    

class StudentSubjectRecommendationManager(BaseManager):
    def select_student_recommendations(self, student_id, subject_id=None, include_archived=False) -> List[StudentSubjectRecommendation]:
        if subject_id:
            return StudentSubjectRecommendation.query.filter_by(student_id=student_id, subject_id=subject_id, is_archived=include_archived).all()
        return StudentSubjectRecommendation.query.filter_by(student_id=student_id, subject_id=subject_id, is_archived=include_archived).all()
    
    def insert_student_recommendation(self, student_id, subject_id, topic_id, recommendation_level) -> StudentSubjectRecommendation:
        new_recommendation = StudentSubjectRecommendation(
            student_id=student_id,
            subject_id=subject_id,
            topic_id=topic_id,
            recommendation_level=recommendation_level
        )
        self.save(new_recommendation)
        return new_recommendation

    def insert_multiple_recommendations(self, entities: List[Dict]):
        to_save: List[StudentSubjectRecommendation] = []
        for entity in entities:
            to_save.append(
                StudentSubjectRecommendation(**entity)
            )
        self.save_multiple(to_save)
        return [entity.to_json() for entity in to_save]



sts_manager = StudentTopicScoresManager()
sbs_manager = StudentBestSubjectManager()
ssr_manager = StudentSubjectRecommendationManager()