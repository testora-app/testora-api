from app._shared.operations import BaseManager
from app.analytics.models import StudentTopicScores, StudentBestSubject, StudentSubjectRecommendation, StudentSession
from sqlalchemy import func
from sqlalchemy.sql import case, func as sqlfunc
from typing import  List, Dict, Union

from datetime import datetime, timedelta, timezone
from logging import info as log_info


class StudentTopicScoresManager(BaseManager):

    def select_student_topic_score_history(self, student_id, topic_id=None)-> List[StudentTopicScores]:
        if topic_id:
            return StudentTopicScores.query.filter_by(student_id=student_id, topic_id=topic_id).all()
        return StudentTopicScores.query.filter_by(student_id=student_id).all()
    
    def select_student_topic_score_sepcific(self, student_id, subject_id, test_id, topic_id) -> StudentTopicScores:
        return StudentTopicScores.query.filter_by(student_id=student_id, subject_id=subject_id, test_id=test_id, topic_id=topic_id).first()
    
    def insert_student_topic_score(self, student_id, subject_id, test_id, topic_id, score_acquired) -> StudentTopicScores:
        new_score = StudentTopicScores(
            student_id=student_id,
            subject_id=subject_id,
            test_id=test_id,
            topic_id=topic_id,
            score_acquired=score_acquired
        )

        self.save(new_score, upsert=True)
        return new_score
    
    def insert_multiple_student_topic_scores(self, entities: List[Dict], upsert=False):
        to_check = [StudentTopicScores(**entity) for entity in entities] 
        to_save = []
        for entity in to_check:
            topic_score = self.select_student_topic_score_sepcific(entity.student_id, entity.subject_id, entity.test_id, entity.topic_id)
            if not topic_score:
                to_save.append(entity)
            else:
                topic_score.score_acquired = entity.score_acquired
                self.save(topic_score)

        self.save_multiple(to_save)
        return [entity.to_json() for entity in to_save + to_check]
    
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
    
    def get_topic_performance(self, student_id=None, subject_id=None) -> List[Dict]:
        query = (
            StudentSubjectRecommendation.query
            .with_entities(
                StudentSubjectRecommendation.topic_id,
                StudentSubjectRecommendation.subject_id,
                sqlfunc.count(case((StudentSubjectRecommendation.recommendation_level == 'low', 1))).label('low_count'),
                sqlfunc.count(case((StudentSubjectRecommendation.recommendation_level == 'moderate', 1))).label('moderate_count'),
                sqlfunc.count(case((StudentSubjectRecommendation.recommendation_level == 'high', 1))).label('high_count')
            )
        )

        query = query.filter(StudentSubjectRecommendation.is_archived == False)

        if student_id:
            query = query.filter_by(student_id=student_id)
        if subject_id: 
            query = query.filter_by(subject_id=subject_id)

        return query.group_by(StudentSubjectRecommendation.topic_id, StudentSubjectRecommendation.subject_id).all()



#region Session

class StudentSessionManager(BaseManager):
    def select_student_session_history(self, student_id, date=None) -> Union[List[StudentSession], StudentSession]:
        if date:
            return StudentSession.query.filter_by(student_id=student_id, date=date).first()
        return StudentSession.query.filter_by(student_id=student_id).all()
    
    def add_new_student_session(self, student_id, date) -> StudentSession:
        new_session = StudentSession(
            student_id=student_id,
            date=date
        )
        self.save(new_session)
        return new_session
    

    def compare_session(self, student_id):
        from app.extensions import db
        now = datetime.now(timezone.utc)

        # Calculate the start of the current week (e.g., assuming weeks start on Monday)
        start_of_this_week = now - timedelta(days=now.weekday())

        # Calculate the start of the previous week
        start_of_last_week = start_of_this_week - timedelta(weeks=1)

        # Query the total time spent between the start of last week and the start of this week
        last_week_time = db.session.query(db.func.sum(StudentSession.duration)).filter(
            StudentSession.created_at.between(start_of_last_week, start_of_this_week), StudentSession.student_id == student_id).scalar()
        
        # Query the total time spent from the start of this week to now
        time_spent_this_week = db.session.query(db.func.sum(StudentSession.duration)).filter(
            StudentSession.created_at.between(start_of_this_week, now), StudentSession.student_id == student_id).scalar()
        
        return last_week_time, time_spent_this_week

#endregion session


sts_manager = StudentTopicScoresManager()
sbs_manager = StudentBestSubjectManager()
ssr_manager = StudentSubjectRecommendationManager()
ssm_manager = StudentSessionManager()