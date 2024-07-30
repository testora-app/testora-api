from app.analytics.operations import sts_manager
from typing import List, Dict
from app._shared.decorators import async_method

class TopicAnalytics:
    
    @async_method
    @staticmethod
    def save_topic_scores_for_student(student_id, subject_id, test_id, test_scores: List[Dict]):
        '''
            test_scores -- List[Dict[]]
            [{
                'topic_id': score
            }]
        '''
        scores_to_save = []

        for score in test_scores:
            scores_to_save.append(
                {
                    'student_id': student_id,
                    'subject_id': subject_id,
                    'test_id': test_id,
                    'topic_id': score.keys()[0],
                    'score_acquired': score.values()[0]
                }
            )
        return sts_manager.insert_multiple_student_topic_scores(scores_to_save)
