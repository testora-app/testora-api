"""
Adaptive Test Question Generation Service

This service analyzes student performance from recent tests and generates
adaptive question distributions that focus on weak areas while maintaining
minimum coverage requirements.
"""

from collections import defaultdict
from typing import Dict, List
from datetime import datetime
import random

from app.extensions import db
from app.test.models import Test

class PerformanceAnalyzer:
    """Analyzes student performance to identify weak topics and levels"""
    
    PERFORMANCE_BANDS = {
        "highly_proficient": 80,
        "proficient": 70,
        "approaching_proficient": 65,
        "developing": 50,
        "emerging": 0,
    }
    
    @classmethod
    def analyze_recent_performance(
        cls, 
        student_id: int, 
        subject_id: int, 
        lookback_tests: int = 5
    ) -> Dict:
        """
        Analyze the last N tests to determine topic and level weaknesses
        
        Returns:
        {
            'topic_weights': {topic_id: weight},  # Higher weight = needs more practice
            'level_weights': {level: weight},     # Higher weight = needs more practice
            'mastered_topics': [topic_ids],       # Topics performing well
            'critical_topics': [topic_ids],       # Topics needing urgent attention
            'recent_questions': {question_id: outcome}  # Recently attempted questions
        }
        """
        from app.test.operations import test_manager
        from app.analytics.models import StudentTopicScores
        
        # Get last N completed tests
        recent_tests = (
            db.session.query(Test)
            .filter(
                Test.student_id == student_id,
                Test.subject_id == subject_id,
                Test.is_completed == True
            )
            .order_by(Test.finished_on.desc())
            .limit(lookback_tests)
            .all()
        )
        
        if not recent_tests:
            return cls._default_weights(subject_id)
        
        # Analyze topic performance
        topic_scores = defaultdict(list)
        level_scores = defaultdict(list)
        question_history = {}
        
        for test in recent_tests:
            # Get topic scores for this test
            test_topic_scores = (
                db.session.query(StudentTopicScores)
                .filter(
                    StudentTopicScores.test_id == test.id,
                    StudentTopicScores.student_id == student_id
                )
                .all()
            )
            
            for score_record in test_topic_scores:
                topic_scores[score_record.topic_id].append(
                    float(score_record.score_acquired)
                )
            
            # Analyze questions for level performance and history
            for question in test.questions:
                topic_id = question.get('topic_id')
                level = question.get('level')
                question_id = question.get('id')
                
                # Track if question was answered correctly
                is_correct = (
                    question.get('student_answer') == question.get('correct_answer')
                )
                
                # Store question history (most recent outcome)
                if question_id not in question_history:
                    question_history[question_id] = {
                        'correct': is_correct,
                        'attempts': 1,
                        'topic_id': topic_id,
                        'level': level,
                        'last_seen': test.finished_on
                    }
                
                # Track level performance
                if level:
                    level_scores[level].append(100 if is_correct else 0)
        
        # Calculate weights
        topic_weights = cls._calculate_topic_weights(topic_scores)
        level_weights = cls._calculate_level_weights(level_scores)
        
        # Identify mastered and critical topics
        mastered_topics = [
            topic_id for topic_id, avg in topic_weights.items()
            if avg >= cls.PERFORMANCE_BANDS['highly_proficient']
        ]
        critical_topics = [
            topic_id for topic_id, avg in topic_weights.items()
            if avg < cls.PERFORMANCE_BANDS['developing']
        ]
        
        return {
            'topic_weights': topic_weights,
            'level_weights': level_weights,
            'mastered_topics': mastered_topics,
            'critical_topics': critical_topics,
            'recent_questions': question_history,
            'topic_scores': topic_scores  # Raw scores for reference
        }
    
    @classmethod
    def _calculate_topic_weights(cls, topic_scores: Dict[int, List[float]]) -> Dict[int, float]:
        """
        Calculate weight for each topic based on average performance
        Lower performance = Higher weight (needs more practice)
        
        Returns: {topic_id: average_score}
        """
        topic_weights = {}
        
        for topic_id, scores in topic_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                topic_weights[topic_id] = avg_score
        
        return topic_weights
    
    @classmethod
    def _calculate_level_weights(cls, level_scores: Dict[int, List[float]]) -> Dict[int, float]:
        """
        Calculate weight for each level based on average performance
        
        Returns: {level: average_score}
        """
        level_weights = {}
        
        for level, scores in level_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                level_weights[level] = avg_score
        
        return level_weights
    
    @classmethod
    def _default_weights(cls, subject_id: int) -> Dict:
        """Return default weights when no test history exists"""
        return {
            'topic_weights': {},
            'level_weights': {},
            'mastered_topics': [],
            'critical_topics': [],
            'recent_questions': {},
            'topic_scores': {}
        }


class AdaptiveDistributionEngine:
    """Generates adaptive question distributions based on performance analysis"""
    
    @staticmethod
    def generate_adaptive_distribution(
        total_questions: int,
        student_level: int,
        performance_data: Dict,
        min_per_level: int = 2
    ) -> Dict[int, int]:
        """
        Generate question distribution across levels based on performance
        
        Args:
            total_questions: Total number of questions to generate
            student_level: Current student level (max level they can access)
            performance_data: Output from PerformanceAnalyzer
            min_per_level: Minimum questions per level
            
        Returns:
            {level: question_count}
        """
        level_weights = performance_data.get('level_weights', {})
        levels = list(range(1, student_level + 1))
        
        # Calculate how many questions needed for minimums
        min_questions_needed = min_per_level * len(levels)
        
        if total_questions <= min_questions_needed:
            # If total questions barely cover minimums, distribute evenly
            return {level: min_per_level for level in levels}
        
        # Allocate minimum questions first
        distribution = {level: min_per_level for level in levels}
        remaining = total_questions - min_questions_needed
        
        # Convert performance scores to weakness scores (invert)
        # Lower performance = higher weakness = more questions needed
        weakness_scores = {}
        for level in levels:
            if level in level_weights:
                # Invert: 100 - score = weakness
                weakness = 100 - level_weights[level]
                weakness_scores[level] = max(weakness, 10)  # Minimum 10 to ensure some distribution
            else:
                # No data for this level, give moderate weight
                weakness_scores[level] = 50
        
        # Normalize weakness scores to sum to 1
        total_weakness = sum(weakness_scores.values())
        normalized_weights = {
            level: weakness / total_weakness 
            for level, weakness in weakness_scores.items()
        }
        
        # Distribute remaining questions based on weakness
        for level in levels:
            additional = int(remaining * normalized_weights[level])
            distribution[level] += additional
        
        # Handle rounding errors - distribute any remaining questions
        distributed_total = sum(distribution.values())
        if distributed_total < total_questions:
            # Add remaining to weakest levels
            sorted_levels = sorted(
                levels, 
                key=lambda x: weakness_scores.get(x, 0), 
                reverse=True
            )
            for i in range(total_questions - distributed_total):
                distribution[sorted_levels[i % len(sorted_levels)]] += 1
        
        return distribution
    
    @staticmethod
    def calculate_question_selection_weight(
        question,
        performance_data: Dict,
        recency_boost: float = 2.0,
        failure_boost: float = 3.0
    ) -> float:
        """
        Calculate selection weight for a specific question
        
        Higher weight = more likely to be selected
        
        Factors:
        - Topic weakness (from performance_data)
        - Recent failures (boost if recently failed)
        - Recency (slight penalty if seen very recently)
        """
        topic_id = question.topic_id
        question_id = question.id
        
        # Base weight from topic performance
        topic_weights = performance_data.get('topic_weights', {})
        if topic_id in topic_weights:
            # Lower score = higher weight (invert)
            base_weight = 100 - topic_weights[topic_id]
        else:
            base_weight = 50  # Neutral weight for unknown topics
        
        # Check question history
        question_history = performance_data.get('recent_questions', {})
        if question_id in question_history:
            history = question_history[question_id]
            
            # Boost if recently failed (retry sooner)
            if not history['correct']:
                base_weight *= failure_boost
            
            # Small penalty if seen very recently (within last test)
            # This prevents immediate repetition while still allowing retry
            days_since_seen = (datetime.utcnow() - history['last_seen']).days
            if days_since_seen < 1:
                base_weight *= 0.5  # Reduce weight for questions seen today
            elif days_since_seen < 3:
                base_weight *= 0.8  # Slight reduction for very recent
        
        return max(base_weight, 1.0)  # Ensure minimum weight of 1


class AdaptiveTestService:
    """Main service for generating adaptive tests"""
    
    @staticmethod
    def generate_adaptive_questions(
        subject_id: int, 
        student_id: int,
        student_level: int
    ) -> List:
        """
        Generate adaptive question set based on student performance
        
        This replaces TestService.generate_random_questions_by_level()
        """
        from app.test.models import Question
        from app.app_admin.models import Topic
        from app._shared.schemas import QuestionsNumberLimiter
        
        # Get total questions needed
        total_questions = QuestionsNumberLimiter.get_question_limit_for_level(
            student_level
        )
        
        # Analyze performance
        performance_data = PerformanceAnalyzer.analyze_recent_performance(
            student_id, subject_id, lookback_tests=5
        )
        
        # Generate adaptive distribution
        level_distribution = AdaptiveDistributionEngine.generate_adaptive_distribution(
            total_questions=total_questions,
            student_level=student_level,
            performance_data=performance_data,
            min_per_level=2
        )
        
        # Select questions for each level with weighted selection
        selected_questions = []
        
        for level, count in level_distribution.items():
            # Get all available questions for this level
            available_questions = (
                db.session.query(Question)
                .join(Topic, Question.topic_id == Topic.id)
                .filter(
                    Topic.level == level,
                    Topic.subject_id == subject_id,
                    Question.is_deleted == False,
                    Question.is_flagged != True
                )
                .all()
            )
            
            if not available_questions:
                continue
            
            # Check if we have enough questions
            if len(available_questions) < count:
                # Not enough questions at this level
                # Fallback: get questions from mastered topics if available
                selected = available_questions  # Take all available
                
                # Try to fill remaining from mastered topics
                shortage = count - len(selected)
                if shortage > 0:
                    mastered_questions = AdaptiveTestService._get_mastered_fallback_questions(
                        subject_id=subject_id,
                        student_level=student_level,
                        needed_count=shortage,
                        performance_data=performance_data,
                        exclude_ids=[q.id for q in selected]
                    )
                    selected.extend(mastered_questions)
            else:
                # Weighted selection
                selected = AdaptiveTestService._weighted_question_selection(
                    available_questions=available_questions,
                    count=count,
                    performance_data=performance_data
                )
            
            selected_questions.extend(selected)
        
        # Final shuffle to randomize order (but maintain weighted selection)
        random.shuffle(selected_questions)
        
        return selected_questions
    
    @staticmethod
    def _weighted_question_selection(
        available_questions: List,
        count: int,
        performance_data: Dict
    ) -> List:
        """
        Select questions using weighted random selection
        Questions from weaker topics have higher probability of selection
        """
        # Calculate weights for all questions
        weights = []
        for question in available_questions:
            weight = AdaptiveDistributionEngine.calculate_question_selection_weight(
                question, performance_data
            )
            weights.append(weight)
        
        # Weighted random selection without replacement
        selected = []
        questions_copy = available_questions.copy()
        weights_copy = weights.copy()
        
        for _ in range(min(count, len(questions_copy))):
            # Use weights for selection probability
            total_weight = sum(weights_copy)
            probabilities = [w / total_weight for w in weights_copy]
            
            # Select one question based on probabilities
            selected_idx = random.choices(
                range(len(questions_copy)), 
                weights=probabilities, 
                k=1
            )[0]
            
            selected.append(questions_copy[selected_idx])
            
            # Remove selected question
            questions_copy.pop(selected_idx)
            weights_copy.pop(selected_idx)
        
        return selected
    
    @staticmethod
    def _get_mastered_fallback_questions(
        subject_id: int,
        student_level: int,
        needed_count: int,
        performance_data: Dict,
        exclude_ids: List[int]
    ) -> List:
        """
        Fallback: Get questions from mastered topics when weak topics 
        don't have enough questions
        
        Strategy: Pick from topics with LOWEST mastered average 
        (least mastered among the mastered)
        """
        from app.test.models import Question
        from app.app_admin.models import Topic
        
        mastered_topics = performance_data.get('mastered_topics', [])
        
        if not mastered_topics:
            # No mastered topics, just get any available questions
            fallback_questions = (
                db.session.query(Question)
                .join(Topic, Question.topic_id == Topic.id)
                .filter(
                    Topic.subject_id == subject_id,
                    Topic.level <= student_level,
                    Question.is_deleted == False,
                    Question.is_flagged != True,
                    ~Question.id.in_(exclude_ids)
                )
                .order_by(db.func.random())
                .limit(needed_count)
                .all()
            )
            return fallback_questions
        
        # Sort mastered topics by score (lowest first)
        topic_scores = performance_data.get('topic_weights', {})
        sorted_mastered = sorted(
            mastered_topics,
            key=lambda t: topic_scores.get(t, 100)
        )
        
        # Get questions from least mastered topics first
        selected = []
        for topic_id in sorted_mastered:
            if len(selected) >= needed_count:
                break
            
            questions = (
                db.session.query(Question)
                .join(Topic, Question.topic_id == Topic.id)
                .filter(
                    Topic.id == topic_id,
                    Topic.level <= student_level,
                    Question.is_deleted == False,
                    Question.is_flagged != True,
                    ~Question.id.in_(exclude_ids + [q.id for q in selected])
                )
                .order_by(db.func.random())
                .limit(needed_count - len(selected))
                .all()
            )
            selected.extend(questions)
        
        return selected


class AdaptiveTestMetrics:
    """Track and report on adaptive test effectiveness"""
    
    @staticmethod
    def calculate_adaptation_metrics(test_id: int) -> Dict:
        """
        Calculate metrics showing how well the adaptive system worked
        for a specific test
        
        Returns metrics like:
        - Improvement in weak areas
        - Coverage of recommended topics
        - Question distribution effectiveness
        """
        from app.test.operations import test_manager
        
        test = test_manager.get_test_by_id(test_id)
        
        # Analyze question distribution
        level_distribution = defaultdict(int)
        topic_distribution = defaultdict(int)
        weak_topic_coverage = 0
        
        for question in test.questions:
            level = question.get('level')
            topic_id = question.get('topic_id')
            
            if level:
                level_distribution[level] += 1
            if topic_id:
                topic_distribution[topic_id] += 1
        
        return {
            'level_distribution': dict(level_distribution),
            'topic_distribution': dict(topic_distribution),
            'total_questions': len(test.questions),
            'score': float(test.score_acquired)
        }
    
    @staticmethod
    def get_improvement_trend(student_id: int, subject_id: int, tests: int = 5) -> Dict:
        """
        Analyze if student is improving over recent tests
        
        Returns trend data showing score progression
        """
        recent_tests = (
            db.session.query(Test)
            .filter(
                Test.student_id == student_id,
                Test.subject_id == subject_id,
                Test.is_completed == True
            )
            .order_by(Test.finished_on.desc())
            .limit(tests)
            .all()
        )
        
        if len(recent_tests) < 2:
            return {'trend': 'insufficient_data', 'tests': len(recent_tests)}
        
        scores = [float(test.score_acquired) for test in reversed(recent_tests)]
        
        # Calculate trend
        if len(scores) >= 3:
            # Use simple linear trend
            avg_first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            avg_second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            
            if avg_second_half > avg_first_half + 5:
                trend = 'improving'
            elif avg_second_half < avg_first_half - 5:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            # Just compare first and last
            if scores[-1] > scores[0] + 5:
                trend = 'improving'
            elif scores[-1] < scores[0] - 5:
                trend = 'declining'
            else:
                trend = 'stable'
        
        return {
            'trend': trend,
            'scores': scores,
            'average': sum(scores) / len(scores),
            'latest': scores[-1],
            'earliest': scores[0],
            'change': scores[-1] - scores[0]
        }
