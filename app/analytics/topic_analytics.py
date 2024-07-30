from app.analytics.operations import sts_manager
from typing import List, Dict, Tuple
from app._shared.decorators import async_method
import ast


class RecommendationLevels:
    high = 'highly'
    moderate = 'moderately'
    low = 'lowly'

    @staticmethod
    def calculate_recommendation_level(diff):
        # difference between highest and lowest score
        # if the difference is bad then it's really bad
        # if it's not that bad...then it's fine
        if diff >= 0 and diff < 4:
            return RecommendationLevels.low
        elif diff > 3 and diff < 7:
            return RecommendationLevels.moderate
        else:
            return RecommendationLevels.high
        

    @staticmethod
    def calcuate_recommendation_level_for_avg(score, recommendation=True):
        # if we their average score is really low, it means they're recommended to take that topic
        # else it means their proficient

        if score > 80:
            return RecommendationLevels.low if recommendation else RecommendationLevels.high 
        elif score > 50 and score < 79:
            return RecommendationLevels.moderate
        elif score <= 50:
            return RecommendationLevels.high if recommendation else RecommendationLevels.low


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
    

    @staticmethod
    def __calculate_topic_recommendations(test_scores: List[Dict]) -> Tuple[List[int], List[int], int]:
        '''test_scores -- List[Dict[]]
            [{
                'topic_id': score
            }]
        '''
        min_value = float('inf')
        max_value = float('-inf')
        min_keys = set()
        max_keys = set()  # Use a set to handle multiple keys with the same maximum value

        for d in test_scores:
            for key, value in d.items():
                # Check for maximum value
                if value > max_value:
                    max_value = value
                    max_keys = {key}
                elif value == max_value:
                    max_keys.add(key)

                # Check for minimum value
                if value < min_value:
                    min_value = value
                    min_keys = [key]
                elif value == min_value:
                    min_keys.add(key)

        # Convert set to list for consistency
        max_keys = list(max_keys)
        min_keys = list(min_keys)
        
        return max_keys, min_keys, max_value - min_value
    

    @staticmethod
    def __calculate_topic_recommendations_per_avg(test_scores: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        '''test_scores -- List[Dict[]]
            [{
                'topic_id': score
            }]
        '''
        min_value = float('inf')
        max_value = float('-inf')
        min_kv = list
        max_kv = list  # Use a set to handle multiple keys with the same maximum value

        for d in test_scores:
            for key, value in d.items():
                # Check for maximum value
                if value > max_value:
                    max_value = value
                    max_kv.append({key: value})
                elif value == max_value:
                    max_kv.append({key: value})

                # Check for minimum value
                if value < min_value:
                    min_value = value
                    min_kv.append({key: value})
                elif value == min_value:
                    min_kv.append({key: value})

        
        return max_kv, min_kv
    

    # do some analytics for the test based, and save it in the test metadata righttt?
    @async_method
    @staticmethod
    def test_level_topic_analytics(test_id, test_scores):
        from app.test.operations import test_manager
        from app.admin.operations import topic_manager

        test = test_manager.get_test_by_id(test_id)

        metadata = ast.literal_eval(test.meta)

        best_topics, worst_topics, diff = TopicAnalytics.__calculate_topic_recommendations(test_scores)
        recommendation_level = RecommendationLevels.calculate_recommendation_level(diff)

        topic_analytics = {
            'best_topics': [topic_manager.get_topic_by_id(id).to_json() for id in best_topics],
            'recommendations':[
                {
                    'topic': topic_manager.get_topic_by_id(id).name,
                    'level': recommendation_level
                } for id in worst_topics
            ]
        }

        metadata['topic_analytics'] = topic_analytics
        test.meta = metadata
        test.save()

    @staticmethod
    def student_level_topic_analytics(student_id, subject_id):
        
        # get the averages from topic_ids for the subject_id
        averages : List[Tuple[int, float]] = sts_manager.get_averages_for_topics_by_subject_id(student_id, subject_id)

        test_scores = []

        for topic_id, score in averages:
            test_scores.append({
                topic_id: score
            })
        
        best_topics, worst_topics  = TopicAnalytics.__calculate_topic_recommendations(test_scores)

        proficient = []
        recommended = []

        # fetch the current best topics
        # check if the current best topics, are the same as the old and archive and create new ones if applicable else leave as is

        # get the removed and the added topics
        # archived the removed

        # add the new

        # highest average is best topic
        for best in best_topics:
            pass

        # lowest average is recommended -- check the difference in averages and make the averages
        # fetch the current best topics
        # check if the current best topics, are the same as the old and archive and create new ones if applicable else leave as is

        