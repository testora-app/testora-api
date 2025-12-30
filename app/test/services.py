"""
Updated TestService with Adaptive Question Generation

This is an enhanced version of your TestService that uses the adaptive
question generation system while maintaining backward compatibility.
"""

from collections import defaultdict
from typing import Dict, List
import random
from .adaptive_test_service import (
    PerformanceAnalyzer,
    AdaptiveDistributionEngine,
    AdaptiveTestService,
    AdaptiveTestMetrics
)


from app.extensions import db
from app._shared.schemas import ExamModes, QuestionsNumberLimiter, QuestionPoints
from app.app_admin.models import Topic
from app.test.models import Question


class TestService:
    """Enhanced TestService with adaptive question generation"""

    @staticmethod
    def is_mode_accessible(exam_mode, student_level):
        # the exam_mode and the level that it is accessible at
        levels = {ExamModes.level: 0, ExamModes.exam: 6}
        # if the student level is greater than or equal to the desired exam mode, allow them else nooo!
        return student_level >= levels[exam_mode]

    # DEPRECATED: Use generate_adaptive_questions instead
    @classmethod
    def __generate_level_counts(cls, total_questions, max_level) -> Dict[int, int]:
        """
        DEPRECATED: This method is kept for backward compatibility only.
        Use AdaptiveDistributionEngine.generate_adaptive_distribution() instead.
        
        The code snippet efficiently distributes a specified number of questions (total_questions) randomly across different levels (1 to max_level)
        This approach ensures that questions are evenly distributed across levels based on the specified parameters.
        It returns a dictionary where each key represents a level, and the value represents the number of questions generated for that level.
        """
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
            number_of_sub = len(question["sub_questions"])
            total_points += (
                question["level"] * (1 + number_of_sub)
            ) * question_multiplier[question["level"]]

        return round(total_points, 2)

    @staticmethod
    def determine_question_points(
        question, main_correct=True, sub_questions_correct=0
    ) -> int:
        question_multiplier = QuestionPoints.get_question_level_points()

        if main_correct:
            return (question["level"] + sub_questions_correct) * question_multiplier[
                question["level"]
            ]
        return sub_questions_correct * question["level"]

    @staticmethod
    def determine_test_duration_in_seconds(max_duration, question_length) -> int:
        if max_duration:
            return max_duration // question_length
        return 3000

    # DEPRECATED: Use generate_adaptive_questions instead
    @staticmethod
    def generate_random_questions_by_level(subject_id, student_level) -> List[Question]:
        """
        DEPRECATED: This method is kept for backward compatibility only.
        Use generate_adaptive_questions() for better, performance-based question selection.
        
        Legacy random question generation method.
        """
        total_questions = QuestionsNumberLimiter.get_question_limit_for_level(
            student_level
        )
        level_counts = TestService.__generate_level_counts(
            total_questions, student_level
        )  # max level is student_level

        questions = []

        for level, count in level_counts.items():
            level_questions = (
                db.session.query(Question)
                .join(Topic, Question.topic_id == Topic.id)
                .filter(
                    Topic.level == level,
                    Topic.subject_id == subject_id,
                    Question.is_deleted == False,
                    Question.is_flagged != True,
                )
                .order_by(db.func.random())
                .limit(count)
                .all()
            )
            questions.extend(level_questions)

        # Shuffle the final list to ensure overall randomness
        random.shuffle(questions)
        return questions
    
    @staticmethod
    def generate_adaptive_questions(
        subject_id: int,
        student_id: int,
        student_level: int,
        use_adaptive: bool = True
    ) -> List[Question]:
        """
        Generate questions using adaptive algorithm based on student performance.
        
        Args:
            subject_id: Subject to generate questions for
            student_id: Student taking the test
            student_level: Current student level
            use_adaptive: If False, falls back to random generation (for testing)
            
        Returns:
            List of Question objects optimized for student's learning needs
        """
        if not use_adaptive:
            # Fallback to legacy random generation
            return TestService.generate_random_questions_by_level(
                subject_id, student_level
            )
        
        return AdaptiveTestService.generate_adaptive_questions(
            subject_id=subject_id,
            student_id=student_id,
            student_level=student_level
        )
    
    @staticmethod
    def get_test_generation_preview(
        subject_id: int,
        student_id: int,
        student_level: int
    ) -> Dict:
        """
        Preview what the adaptive test generation will look like
        without actually generating a test.
        
        Useful for debugging or showing students their focus areas.
        
        Returns:
            {
                'total_questions': int,
                'level_distribution': {level: count},
                'focus_topics': [topic_names],
                'weak_areas': [topic_names],
                'mastered_areas': [topic_names],
                'performance_summary': {...}
            }
        """
        from app.app_admin.operations import topic_manager
        
        # Analyze performance
        performance_data = PerformanceAnalyzer.analyze_recent_performance(
            student_id, subject_id, lookback_tests=5
        )
        
        # Get total questions
        total_questions = QuestionsNumberLimiter.get_question_limit_for_level(
            student_level
        )
        
        # Generate distribution
        level_distribution = AdaptiveDistributionEngine.generate_adaptive_distribution(
            total_questions=total_questions,
            student_level=student_level,
            performance_data=performance_data,
            min_per_level=2
        )
        
        # Get topic names
        critical_topics = [
            topic_manager.get_topic_by_id(tid).name 
            for tid in performance_data['critical_topics']
        ]
        mastered_topics = [
            topic_manager.get_topic_by_id(tid).name 
            for tid in performance_data['mastered_topics']
        ]
        
        # Get weak topics (not critical but below proficient)
        weak_topics = [
            topic_manager.get_topic_by_id(tid).name
            for tid, score in performance_data['topic_weights'].items()
            if score < 70 and tid not in performance_data['critical_topics']
        ]
        
        return {
            'total_questions': total_questions,
            'level_distribution': level_distribution,
            'focus_topics': critical_topics,
            'weak_areas': weak_topics,
            'mastered_areas': mastered_topics,
            'performance_summary': {
                'topics_analyzed': len(performance_data['topic_weights']),
                'tests_analyzed': 5,
                'average_scores': performance_data['topic_weights']
            }
        }
    
    @staticmethod
    def get_student_progress_report(student_id: int, subject_id: int) -> Dict:
        """
        Generate a comprehensive progress report for a student
        
        Returns:
            {
                'improvement_trend': 'improving'|'declining'|'stable',
                'current_performance': {...},
                'recommendations': [...],
                'strengths': [...],
                'areas_for_improvement': [...]
            }
        """
        # Get improvement trend
        trend_data = AdaptiveTestMetrics.get_improvement_trend(
            student_id, subject_id, tests=5
        )
        
        # Get current performance analysis
        performance_data = PerformanceAnalyzer.analyze_recent_performance(
            student_id, subject_id, lookback_tests=5
        )
        
        # Get topic names
        from app.app_admin.operations import topic_manager
        
        strengths = [
            {
                'topic': topic_manager.get_topic_by_id(tid).name,
                'score': performance_data['topic_weights'][tid]
            }
            for tid in performance_data['mastered_topics']
        ]
        
        areas_for_improvement = [
            {
                'topic': topic_manager.get_topic_by_id(tid).name,
                'score': performance_data['topic_weights'][tid],
                'priority': 'high' if tid in performance_data['critical_topics'] else 'medium'
            }
            for tid in performance_data['topic_weights'].keys()
            if tid not in performance_data['mastered_topics']
        ]
        
        # Sort by score (weakest first)
        areas_for_improvement.sort(key=lambda x: x['score'])
        
        return {
            'improvement_trend': trend_data['trend'],
            'trend_details': trend_data,
            'current_performance': {
                'average_score': trend_data.get('average', 0),
                'latest_score': trend_data.get('latest', 0),
                'change_from_first': trend_data.get('change', 0)
            },
            'strengths': strengths,
            'areas_for_improvement': areas_for_improvement[:10],  # Top 10 weak areas
            'recommendations': TestService._generate_recommendations(
                performance_data, trend_data
            )
        }
    
    @staticmethod
    def _generate_recommendations(performance_data: Dict, trend_data: Dict) -> List[str]:
        """Generate personalized recommendations based on performance"""
        recommendations = []
        
        # Trend-based recommendations
        if trend_data['trend'] == 'declining':
            recommendations.append(
                "Your scores have been declining recently. Consider reviewing fundamentals "
                "and taking practice tests more frequently."
            )
        elif trend_data['trend'] == 'improving':
            recommendations.append(
                "Great progress! You're improving steadily. Keep up the consistent practice."
            )
        
        # Critical topics
        if performance_data['critical_topics']:
            recommendations.append(
                f"Focus on {len(performance_data['critical_topics'])} critical topics "
                "where you're scoring below 50%. These need immediate attention."
            )
        
        # Mastered topics
        if len(performance_data['mastered_topics']) > 5:
            recommendations.append(
                "You've mastered several topics! Consider advancing to higher difficulty "
                "levels to continue your growth."
            )
        
        # No data
        if not performance_data['topic_weights']:
            recommendations.append(
                "Complete a few tests to get personalized recommendations based on your performance."
            )
        
        return recommendations
    
    @staticmethod
    def compare_adaptive_vs_random(
        subject_id: int,
        student_id: int,
        student_level: int
    ) -> Dict:
        """
        Compare what questions would be selected by adaptive vs random generation.
        Useful for testing and validation.
        
        Returns:
            {
                'adaptive': {...},
                'random': {...},
                'differences': {...}
            }
        """
        # Get adaptive questions
        adaptive_questions = TestService.generate_adaptive_questions(
            subject_id, student_id, student_level, use_adaptive=True
        )
        
        # Get random questions
        random_questions = TestService.generate_adaptive_questions(
            subject_id, student_id, student_level, use_adaptive=False
        )
        
        # Analyze distributions
        def analyze_distribution(questions):
            level_dist = defaultdict(int)
            topic_dist = defaultdict(int)
            
            for q in questions:
                level_dist[q.level] += 1
                topic_dist[q.topic_id] += 1
            
            return {
                'level_distribution': dict(level_dist),
                'topic_distribution': dict(topic_dist),
                'total': len(questions)
            }
        
        adaptive_analysis = analyze_distribution(adaptive_questions)
        random_analysis = analyze_distribution(random_questions)
        
        # Calculate differences
        level_diff = {}
        for level in set(list(adaptive_analysis['level_distribution'].keys()) + 
                        list(random_analysis['level_distribution'].keys())):
            adaptive_count = adaptive_analysis['level_distribution'].get(level, 0)
            random_count = random_analysis['level_distribution'].get(level, 0)
            level_diff[level] = adaptive_count - random_count
        
        return {
            'adaptive': adaptive_analysis,
            'random': random_analysis,
            'differences': {
                'level_differences': level_diff,
                'adaptive_focuses_on_weak_areas': sum(1 for d in level_diff.values() if d > 0),
                'total_questions': len(adaptive_questions)
            }
        }
    
    @staticmethod
    def mark_test(questions, deduct_points=False):
        from app.test.operations import question_manager
        # we need a way to determine if we're deducting points lost or half points

        points_acquired = 0
        score_acquired = 0  # correct/total * 100

        # recommended topic, recommendation_level = high
        # a break down of topics and the percentage acquired
        total_number = len(questions)

        topic_scores = {question["topic_id"]: 0 for question in questions}
        topic_totals = {question["topic_id"]: 0 for question in questions}

        for question in questions:
            q = question_manager.get_question_by_id(question["id"])
            if not q:
                total_number -= 1
                continue 
            
            main_question_correct = False
            no_subs_correct = 0

            if not q.is_flagged:
                #TODO: MAKE THIS BETTER JOSEPH 
                # current logic: mark main question if it's not flagged
                topic_totals[q.topic_id] += 1
                if q.correct_answer == question["student_answer"]:
                    main_question_correct = True
                    score_acquired += 1
                    topic_scores[q.topic_id] += 1
                else:
                    if deduct_points:
                        points_acquired -= TestService.determine_question_points(question)

            # mark sub questions if any
            if len(question["sub_questions"]) > 0:
                total_number += len(question["sub_questions"])
                for sub in question["sub_questions"]:
                    s = question_manager.get_sub_question_by_id(sub["id"])
                    if not s:
                        total_number -= 1
                        continue

                    if s.is_flagged:
                        continue  # skip flagged sub questions
                    topic_totals[q.topic_id] += 1
                    sub["correct_answer"] = s.correct_answer
                    if s.correct_answer == sub["student_answer"]:
                        no_subs_correct += 1
                        topic_scores[q.topic_id] += 1
                    else:
                        if deduct_points:
                            points_acquired -= 1

            points = round(
                TestService.determine_question_points(
                    question,
                    main_correct=main_question_correct,
                    sub_questions_correct=no_subs_correct,
                ),
                2,
            )
            points_acquired += points
            question["correct_answer"] = q.correct_answer
            question["points"] = points
            score_acquired += no_subs_correct

        score_acquired = (score_acquired / total_number) * 100  # correct/total * 100

        return {
            "questions": questions,
            "points_acquired": round(points_acquired, 2),
            "score_acquired": score_acquired,
            "topic_scores": topic_scores,
            "topic_totals": topic_totals,
        }
