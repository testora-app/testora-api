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
        # if we their average score is really low, it means they're recommended to take that topic
        # else it means their proficient

        if score > 80:
            return (
                RecommendationLevels.low
                if recommendation
                else RecommendationLevels.high
            )
        elif score > 50 and score < 79:
            return RecommendationLevels.moderate
        elif score <= 50:
            return (
                RecommendationLevels.high
                if recommendation
                else RecommendationLevels.low
            )


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
        student_id, subject_id, test_id, test_scores: Dict
    ):
        """
        test_scores -- Dict[]
        [{
            'topic_id': score
        }]
        """
        scores_to_save = []
        for topic_id, score in test_scores.items():
            scores_to_save.append(
                {
                    "student_id": student_id,
                    "subject_id": subject_id,
                    "test_id": test_id,
                    "topic_id": topic_id,
                    "score_acquired": score,
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
    def test_level_topic_analytics(test_id, test_scores: Dict):
        from app.test.operations import test_manager
        from app.admin.operations import topic_manager

        test = test_manager.get_test_by_id(test_id)

        best_topics, worst_topics, diff = (
            TopicAnalytics.__calculate_topic_recommendations(test_scores)
        )
        recommendation_level = RecommendationLevels.calculate_recommendation_level(diff)

        topic_analytics = {
            "best_topics": [
                topic_manager.get_topic_by_id(id).name for id in best_topics
            ],
            "recommendations": [
                {
                    "topic": topic_manager.get_topic_by_id(id).name,
                    "level": recommendation_level,
                }
                for id in worst_topics
            ],
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

        test_scores = []

        for topic_id, score in averages:
            test_scores.append({topic_id: score})

        best_topics, worst_topics = (
            TopicAnalytics.__calculate_topic_recommendations_per_avg(test_scores)
        )

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

        # add the new recommendations and best topics
        for topic_id in recommended_comparisons["added"]:
            ssr_manager.insert_student_recommendation(
                student_id,
                subject_id,
                topic_id,
                RecommendationLevels.calculate_recommendation_level_for_avg(
                    worst_objs[topic_id], recommendation=True
                ),
            )

        for topic_id in proficient_comparisons["added"]:
            sbs_manager.insert_student_best(
                student_id,
                subject_id,
                topic_id,
                RecommendationLevels.calculate_recommendation_level_for_avg(
                    best_objs[topic_id]
                ),
            )
