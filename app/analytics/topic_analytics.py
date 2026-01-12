from app.analytics.operations import sts_manager, sbs_manager, ssr_manager
from typing import List, Dict, Tuple
from app._shared.decorators import async_method
import json


class RecommendationLevels:
    high = "highly"
    moderate = "moderately"
    low = "lowly"

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
    def calculate_recommendation_level_for_avg(score, recommendation=True):
        """
        Calculate recommendation or proficiency level based on percentage score.
        
        For recommendations (topics to work on):
        - < 50% = highly recommended
        - 50-70% = moderately recommended
        - 70-85% = low priority recommendation
        - 85%+ = None (not saved)
        
        For proficiency (best subjects):
        - 80%+ = highly proficient
        - 65-80% = moderately proficient
        - 50-65% = low proficient
        - < 50% = None (not tracked)
        """
        if recommendation:
            # For recommendations (lower scores = higher priority)
            if score < 50:
                return RecommendationLevels.high
            elif score < 70:
                return RecommendationLevels.moderate
            elif score < 85:
                return RecommendationLevels.low
            else:
                return None  # Above 85% - no recommendation needed
        else:
            # For proficiency (higher scores = higher proficiency)
            if score >= 80:
                return RecommendationLevels.high
            elif score >= 65:
                return RecommendationLevels.moderate
            elif score >= 50:
                return RecommendationLevels.low
            else:
                return None  # Below 50% - not proficient


class TopicAnalytics:
    @staticmethod
    def __compare(old_list, new_list):
        old_set = set(old_list)
        new_set = set(new_list)

        added = list(new_set - old_set)
        removed = list(old_set - new_set)
        remaining = list(old_set & new_set)

        return {"added": added, "removed": removed, "remaining": remaining}

    # @async_method
    @staticmethod
    def save_topic_scores_for_student(
        student_id, subject_id, test_id, test_scores: Dict, topic_totals: Dict
    ):
        """
        test_scores -- Dict[] of correct answers per topic
        topic_totals -- Dict[] of total questions per topic
        Calculate percentage: (score/total * 100) floored to 2 decimal places
        [{
            'topic_id': score
        }]
        """
        scores_to_save = []
        for topic_id, score in test_scores.items():
            total = topic_totals.get(topic_id, 1)  # Avoid division by zero
            if total > 0:
                percentage = (score / total) * 100
                percentage = round(percentage, 2)  # Floor to 2 decimal places
            else:
                percentage = 0.0
            
            scores_to_save.append(
                {
                    "student_id": student_id,
                    "subject_id": subject_id,
                    "test_id": test_id,
                    "topic_id": topic_id,
                    "score_acquired": percentage,
                }
            )
        return sts_manager.insert_multiple_student_topic_scores(
            scores_to_save, upsert=True
        )

    @staticmethod
    def __calculate_topic_recommendations(
        test_scores: Dict,
    ) -> Tuple[List[int], List[int], int]:
        """test_scores -- List[Dict[]]
        [{
            'topic_id': score
        }]
        """
        # TODO: improve this to only take subjects where the student gets wrongs, so if i dont get any wrongs don't recommend it
        min_value = float("inf")
        max_value = float("-inf")
        min_keys = set()
        max_keys = (
            set()
        )  # Use a set to handle multiple keys with the same maximum value

        for key, value in test_scores.items():
            # Check for maximum value
            if value > max_value:
                max_value = value
                max_keys = {key}
            elif value == max_value:
                max_keys.add(key)

            # Check for minimum value
            if value < min_value:
                min_value = value
                min_keys = {key}
            elif value == min_value:
                min_keys.add(key)

        # Convert set to list for consistency
        max_keys = list(max_keys)
        min_keys = list(min_keys)

        return max_keys, min_keys, max_value - min_value

    @staticmethod
    def __calculate_topic_recommendations_per_avg(
        test_scores: List[Dict],
    ) -> Tuple[List[Dict], List[Dict]]:
        """test_scores -- List[Dict[]]
        [{
            'topic_id': score
        }]
        """
        min_value = float("inf")
        max_value = float("-inf")
        min_kv = []
        max_kv = []  # Use a set to handle multiple keys with the same maximum value

        for s in test_scores:
            for key, value in s.items():
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

    # do some analytics for the test based, and save it in the test metadata right?
    # @async_method
    @staticmethod
    def test_level_topic_analytics(test_id, test_scores: Dict, topic_totals: Dict):
        """
        Analyze test performance using percentage-based thresholds.
        
        Categorizes topics into:
        - Best topics: 85%+ (mastered)
        - Highly recommended: < 50% (critical need)
        - Moderately recommended: 50-70%
        - Low priority recommended: 70-85%
        """
        from app.test.operations import test_manager
        from app.app_admin.operations import topic_manager

        test = test_manager.get_test_by_id(test_id)

        # Calculate percentages for each topic
        topic_percentages = {}
        for topic_id, score in test_scores.items():
            total = topic_totals.get(topic_id, 1)
            if total > 0:
                percentage = (score / total) * 100
                topic_percentages[topic_id] = round(percentage, 2)
            else:
                topic_percentages[topic_id] = 0.0

        # Categorize topics based on percentage thresholds
        best_topics = []  # 85%+
        highly_recommended = []  # < 50%
        moderately_recommended = []  # 50-70%
        low_recommended = []  # 70-85%

        for topic_id, percentage in topic_percentages.items():
            if percentage >= 85:
                best_topics.append(topic_id)
            elif percentage < 50:
                highly_recommended.append(topic_id)
            elif percentage < 70:
                moderately_recommended.append(topic_id)
            else:  # 70-85%
                low_recommended.append(topic_id)

        # Build recommendations list with levels
        recommendations = []
        
        for topic_id in highly_recommended:
            recommendations.append({
                "topic": topic_manager.get_topic_by_id(topic_id).name,
                "level": RecommendationLevels.high,
            })
        
        for topic_id in moderately_recommended:
            recommendations.append({
                "topic": topic_manager.get_topic_by_id(topic_id).name,
                "level": RecommendationLevels.moderate,
            })
        
        for topic_id in low_recommended:
            recommendations.append({
                "topic": topic_manager.get_topic_by_id(topic_id).name,
                "level": RecommendationLevels.low,
            })

        topic_analytics = {
            "best_topics": [
                topic_manager.get_topic_by_id(id).name for id in best_topics
            ],
            "recommendations": recommendations,
        }
        
        meta = {}
        meta["out_time"] = test.meta.get("out_time", 0)
        meta["topic_analytics"] = topic_analytics
        test.meta = meta
        test.save()

    @staticmethod
    def __archive_the_removed(removed_obj: List):
        for entity in removed_obj:
            entity.is_archived = True
            entity.save()

    @staticmethod
    def student_level_topic_analytics(student_id, subject_id):

        # get the averages from topic_ids for the subject_id
        averages: List[Tuple[int, float]] = (
            sts_manager.get_averages_for_topics_by_subject_id(student_id, subject_id)
        )

        # Filter topics based on thresholds
        # For proficiency: only include topics with score >= 50%
        # For recommendations: only include topics with score < 85%
        proficient_scores = []
        recommendation_scores = []

        for topic_id, score in averages:
            # Check if topic qualifies for proficiency tracking (>= 50%)
            if score >= 50:
                proficient_scores.append({topic_id: score})
            
            # Check if topic qualifies for recommendation (< 85%)
            if score < 85:
                recommendation_scores.append({topic_id: score})

        # Find best and worst topics from filtered lists
        best_topics = []
        worst_topics = []
        
        if proficient_scores:
            best_topics, _ = TopicAnalytics.__calculate_topic_recommendations_per_avg(proficient_scores)
        
        if recommendation_scores:
            _, worst_topics = TopicAnalytics.__calculate_topic_recommendations_per_avg(recommendation_scores)

        proficient = sbs_manager.select_student_best(student_id, subject_id)
        recommended = ssr_manager.select_student_recommendations(student_id, subject_id)

        # fetch the current best topics
        # check if the current best topics, are the same as the old and archive and create new ones if applicable else leave as is

        proficient_comparisons = TopicAnalytics.__compare(
            [p.id for p in proficient], [list(b.keys())[0] for b in best_topics]
        )
        recommended_comparisons = TopicAnalytics.__compare(
            [r.id for r in recommended], [list(r.keys())[0] for r in worst_topics]
        )

        # get the removed and the added topics
        # archived the removed
        TopicAnalytics.__archive_the_removed(
            [p for p in proficient if p.id in proficient_comparisons["removed"]]
        )
        TopicAnalytics.__archive_the_removed(
            [r for r in recommended if r.id in recommended_comparisons["removed"]]
        )

        worst_objs = {}
        best_objs = {}

        for t in worst_topics:
            key: List = list(t.keys())
            worst_objs[key[0]] = list(t.values())[0]

        for t in best_topics:
            key: List = list(t.keys())
            best_objs[key[0]] = list(t.values())[0]

        # add the new recommendations and best topics (only if they meet the threshold)
        for topic_id in recommended_comparisons["added"]:
            recommendation_level = RecommendationLevels.calculate_recommendation_level_for_avg(
                worst_objs[topic_id], recommendation=True
            )
            # Only save if the score is below 85% (recommendation_level is not None)
            if recommendation_level is not None:
                ssr_manager.insert_student_recommendation(
                    student_id,
                    subject_id,
                    topic_id,
                    recommendation_level,
                )

        for topic_id in proficient_comparisons["added"]:
            proficiency_level = RecommendationLevels.calculate_recommendation_level_for_avg(
                best_objs[topic_id], recommendation=False
            )
            # Only save if the score is at least 50% (proficiency_level is not None)
            if proficiency_level is not None:
                sbs_manager.insert_student_best(
                    student_id,
                    subject_id,
                    topic_id,
                    proficiency_level,
                )
