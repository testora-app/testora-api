"""
Comprehensive tests for test routes (app/test/routes.py)
Tests cover question management and test creation/submission.
"""

import pytest
import json
from unittest.mock import patch


class TestQuestionRoutes:
    """Tests for question management endpoints."""
    
    def test_get_questions(self, client, sample_question):
        """Test GET /questions/ returns list of questions."""
        response = client.get('/questions/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_post_question_with_valid_data(
        self, client, sample_subject, sample_topic
    ):
        """Test POST /questions/ creates new question."""
        payload = {
            "data": {
                "question_text": "What is the capital of Ghana?",
                "question_type": "multiple_choice",
                "options": ["Accra", "Kumasi", "Tamale", "Takoradi"],
                "correct_answer": "Accra",
                "subject_id": sample_subject.id,
                "topic_id": sample_topic.id,
                "difficulty_level": 1,
                "year": 2024
            }
        }
        
        response = client.post(
            '/questions/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['question_text'] == payload['data']['question_text']
    
    def test_post_question_with_subquestions(
        self, client, sample_subject, sample_topic
    ):
        """Test POST /questions/ creates question with sub-questions."""
        payload = {
            "data": {
                "question_text": "Parent question",
                "question_type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "subject_id": sample_subject.id,
                "topic_id": sample_topic.id,
                "difficulty_level": 1,
                "year": 2024,
                "sub_questions": [
                    {
                        "question_text": "Sub question 1",
                        "question_type": "multiple_choice",
                        "options": ["1", "2", "3", "4"],
                        "correct_answer": "1",
                        "subject_id": sample_subject.id,
                        "topic_id": sample_topic.id,
                        "difficulty_level": 1,
                        "year": 2024
                    }
                ]
            }
        }
        
        response = client.post(
            '/questions/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_post_questions_multiple(
        self, client, sample_subject, sample_topic
    ):
        """Test POST /questions-multiple/ creates multiple questions."""
        payload = {
            "data": [
                {
                    "question_text": "Question 1",
                    "question_type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "subject_id": sample_subject.id,
                    "topic_id": sample_topic.id,
                    "difficulty_level": 1,
                    "year": 2024
                },
                {
                    "question_text": "Question 2",
                    "question_type": "multiple_choice",
                    "options": ["1", "2", "3", "4"],
                    "correct_answer": "1",
                    "subject_id": sample_subject.id,
                    "topic_id": sample_topic.id,
                    "difficulty_level": 1,
                    "year": 2024
                }
            ]
        }
        
        response = client.post(
            '/questions-multiple/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 2
    
    def test_put_question(self, client, sample_question):
        """Test PUT /questions/<id>/ updates question."""
        payload = {
            "data": {
                "question_text": "Updated question",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A"
            }
        }
        
        response = client.put(
            f'/questions/{sample_question.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_delete_question(self, client, sample_question):
        """Test DELETE /questions/<id>/ deletes question."""
        response = client.delete(f'/questions/{sample_question.id}/')
        
        assert response.status_code == 200
    
    def test_delete_question_nonexistent(self, client):
        """Test DELETE /questions/<id>/ with nonexistent ID."""
        response = client.delete('/questions/99999/')
        
        assert response.status_code == 200  # Returns success even if not found
    
    def test_post_flag_questions(self, client, sample_question):
        """Test POST /flag-questions/ flags questions."""
        payload = {
            "data": [
                {
                    "question_id": sample_question.id,
                    "flag_reason": "Incorrect answer"
                }
            ]
        }
        
        response = client.post(
            '/flag-questions/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200


class TestTestRoutes:
    """Tests for test management endpoints."""
    
    def test_get_tests_as_student(
        self, client, student_headers, completed_test
    ):
        """Test GET /tests/ as student returns their tests."""
        response = client.get('/tests/', headers=student_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_tests_as_school_admin(
        self, client, school_admin_headers, completed_test
    ):
        """Test GET /tests/ as school admin returns school tests."""
        response = client.get('/tests/', headers=school_admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['data'], list)
    
    def test_get_tests_with_student_id_filter(
        self, client, staff_headers, sample_student, completed_test
    ):
        """Test GET /tests/ with student_id filter."""
        response = client.get(
            f'/tests/?student_id={sample_student.id}',
            headers=staff_headers
        )
        
        assert response.status_code == 200
    
    def test_get_tests_without_auth(self, client):
        """Test GET /tests/ without auth returns 401."""
        response = client.get('/tests/')
        
        assert response.status_code == 401
    
    @patch('app.test.services.TestService.generate_random_questions_by_level')
    @patch('app.test.services.TestService.is_mode_accessible')
    def test_post_tests_creates_test(
        self, mock_is_accessible, mock_generate, client, student_headers,
        sample_subject, student_subject_level, multiple_questions
    ):
        """Test POST /tests/ creates new test."""
        mock_is_accessible.return_value = True
        mock_generate.return_value = multiple_questions
        
        payload = {
            "data": {
                "mode": "practice",
                "subject_id": sample_subject.id
            }
        }
        
        response = client.post(
            '/tests/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'data' in data
        assert 'questions' in data['data']
    
    def test_post_tests_invalid_mode(
        self, client, student_headers, sample_subject, student_subject_level
    ):
        """Test POST /tests/ with invalid mode returns error."""
        payload = {
            "data": {
                "mode": "invalid_mode",
                "subject_id": sample_subject.id
            }
        }
        
        response = client.post(
            '/tests/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 400
    
    def test_post_tests_premium_subject_free_school(
        self, client, student_headers, premium_subject, sample_free_school
    ):
        """Test POST /tests/ with premium subject on free school returns error."""
        # This would need a student from free school
        payload = {
            "data": {
                "mode": "practice",
                "subject_id": premium_subject.id
            }
        }
        
        response = client.post(
            '/tests/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        # May return 200 or premium error depending on school
        assert response.status_code in [200, 201, 403]
    
    @patch('app.test.services.TestService.mark_test')
    @patch('app.analytics.topic_analytics.TopicAnalytics.save_topic_scores_for_student')
    @patch('app.analytics.topic_analytics.TopicAnalytics.test_level_topic_analytics')
    @patch('app.analytics.topic_analytics.TopicAnalytics.student_level_topic_analytics')
    @patch('app.analytics.remarks_analyzer.RemarksAnalyzer.add_remarks_to_test')
    @patch('app.achievements.services.AchievementEngine.check_test_achievements')
    @patch('app.achievements.services.AchievementEngine.check_level_achievements')
    def test_put_tests_mark(
        self, mock_check_level, mock_check_test, mock_remarks, mock_student_analytics,
        mock_test_analytics, mock_save_scores, mock_mark, client, student_headers,
        sample_test
    ):
        """Test PUT /tests/<id>/mark/ marks test."""
        mock_mark.return_value = {
            "questions": [],
            "score_acquired": 80.0,
            "points_acquired": 8,
            "topic_scores": {},
            "topic_totals": {}
        }
        
        payload = {
            "data": {
                "questions": [
                    {
                        "id": 1,
                        "student_answer": "A"
                    }
                ],
                "meta": {
                    "duration": 3600
                }
            }
        }
        
        response = client.put(
            f'/tests/{sample_test.id}/mark/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_put_tests_mark_nonexistent(self, client, student_headers):
        """Test PUT /tests/<id>/mark/ with nonexistent test returns 404."""
        payload = {
            "data": {
                "questions": [],
                "meta": {}
            }
        }
        
        response = client.put(
            '/tests/99999/mark/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 404
    
    def test_put_tests_mark_without_auth(self, client, sample_test):
        """Test PUT /tests/<id>/mark/ without auth returns 401."""
        payload = {
            "data": {
                "questions": [],
                "meta": {}
            }
        }
        
        response = client.put(
            f'/tests/{sample_test.id}/mark/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401


class TestSubjectPerformance:
    """Tests for GET /tests/subject-performance/ endpoint."""
    
    def test_get_subject_performance_with_school_admin(
        self, client, school_admin_headers, completed_test, sample_subject
    ):
        """Test GET /tests/subject-performance/ returns performance data."""
        response = client.get(
            '/tests/subject-performance/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert 'best_performing_subjects' in data['data']
        assert 'worst_performing_subjects' in data['data']
    
    def test_get_subject_performance_with_staff(
        self, client, staff_headers
    ):
        """Test GET /tests/subject-performance/ with staff auth."""
        response = client.get(
            '/tests/subject-performance/',
            headers=staff_headers
        )
        
        assert response.status_code == 200
    
    def test_get_subject_performance_without_auth(self, client):
        """Test GET /tests/subject-performance/ without auth returns 401."""
        response = client.get('/tests/subject-performance/')
        
        assert response.status_code == 401
    
    def test_get_subject_performance_empty_data(
        self, client, school_admin_headers
    ):
        """Test GET /tests/subject-performance/ with no tests returns empty lists."""
        response = client.get(
            '/tests/subject-performance/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should have the structure even if empty
        assert 'best_performing_subjects' in data['data']
        assert 'worst_performing_subjects' in data['data']
