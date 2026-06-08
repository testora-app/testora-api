"""
Comprehensive tests for test routes (app/test/routes.py)
Tests cover question management and test creation/submission.
"""

import pytest
import json
from unittest.mock import patch


class TestQuestionRoutes:
    """Tests for question management endpoints."""

    def test_get_questions(self, client, auth_headers, sample_question):
        """Test GET /questions/ returns list of questions."""
        response = client.get('/questions/', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_get_questions_without_auth(self, client, sample_question):
        """Test GET /questions/ without auth returns 401."""
        response = client.get('/questions/')
        assert response.status_code == 401

    def test_get_questions_paginated(self, client, auth_headers, multiple_questions):
        """Test GET /questions/ returns one page plus pagination metadata."""
        response = client.get('/questions/?page=1&per_page=4', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 4
        pagination = data['pagination']
        assert pagination['page'] == 1
        assert pagination['per_page'] == 4
        assert pagination['total'] >= 10
        assert pagination['total_pages'] >= 3

    def test_get_questions_search_filters_by_text(
        self, client, auth_headers, multiple_questions
    ):
        """Test GET /questions/?search= only returns matching questions."""
        response = client.get('/questions/?search=question 3', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) >= 1
        assert all('question 3' in q['text'].lower() for q in data['data'])

    def test_get_questions_filter_by_subject(
        self, client, auth_headers, sample_subject, multiple_questions
    ):
        """Test GET /questions/?subject_id= scopes results to that subject."""
        match = client.get(
            f'/questions/?subject_id={sample_subject.id}', headers=auth_headers
        )
        assert match.status_code == 200
        assert len(json.loads(match.data)['data']) >= 10

        miss = client.get('/questions/?subject_id=999999', headers=auth_headers)
        assert miss.status_code == 200
        assert json.loads(miss.data)['data'] == []

    def test_post_question_with_valid_data(
        self, client, auth_headers, sample_subject, sample_topic
    ):
        """Test POST /questions/ creates new question."""
        payload = {
            "data": {
                "text": "What is the capital of Ghana?",
                "possible_answers": ["Accra", "Kumasi", "Tamale", "Takoradi"],
                "correct_answer": "Accra",
                "topic_id": sample_topic.id,
                "points": 1,
                "year": 2024
            }
        }

        response = client.post(
            '/questions/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['text'] == payload['data']['text']

    def test_post_question_with_explanation(
        self, client, auth_headers, sample_subject, sample_topic
    ):
        """Test POST /questions/ persists and returns the explanation."""
        payload = {
            "data": {
                "text": "Which gas do plants absorb during photosynthesis?",
                "possible_answers": ["Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"],
                "correct_answer": "Carbon dioxide",
                "explanation": "Plants take in carbon dioxide and release oxygen during photosynthesis.",
                "topic_id": sample_topic.id,
                "points": 1,
                "year": 2024
            }
        }

        response = client.post(
            '/questions/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['explanation'] == payload['data']['explanation']

    def test_post_multiple_questions_with_explanation(
        self, client, sample_subject, sample_topic
    ):
        """Test POST /questions-multiple/ accepts and stores explanations."""
        payload = {
            "data": [
                {
                    "text": "What is 2 + 2?",
                    "possible_answers": ["2", "3", "4", "5"],
                    "correct_answer": "4",
                    "explanation": "Adding two and two gives four.",
                    "topic_id": sample_topic.id,
                    "points": 1,
                }
            ]
        }

        response = client.post(
            '/questions-multiple/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data'][0]['explanation'] == payload['data'][0]['explanation']

    def test_put_question(self, client, auth_headers, sample_question):
        """Test PUT /questions/<id>/ updates question."""
        payload = {
            "data": {
                "text": "Updated question",
                "possible_answers": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "topic_id": sample_question.topic_id,
                "points": 1
            }
        }

        response = client.put(
            f'/questions/{sample_question.id}/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_delete_question(self, client, auth_headers, sample_question):
        """Test DELETE /questions/<id>/ deletes question."""
        response = client.delete(
            f'/questions/{sample_question.id}/',
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_delete_question_nonexistent(self, client, auth_headers):
        """Test DELETE /questions/<id>/ with nonexistent ID."""
        response = client.delete(
            '/questions/99999/',
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_post_flag_questions(self, client, student_headers, sample_question, mock_mailer):
        """Test POST /flag-questions/ flags questions."""
        payload = {
            "data": [
                {
                    "question_id": sample_question.id,
                    "flag_reason": ["Incorrect answer"]
                }
            ]
        }

        response = client.post(
            '/flag-questions/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )

        assert response.status_code == 200

    def test_post_flag_questions_without_auth(self, client, sample_question):
        """Test POST /flag-questions/ without auth returns 401."""
        payload = {
            "data": [
                {
                    "question_id": sample_question.id,
                    "flag_reason": ["Incorrect answer"]
                }
            ]
        }

        response = client.post(
            '/flag-questions/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 401


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
        assert 'best_performing_subjects' in data['data']
        assert 'worst_performing_subjects' in data['data']
