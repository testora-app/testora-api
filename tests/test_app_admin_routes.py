"""
Comprehensive tests for app_admin routes (app/app_admin/routes.py)
Tests cover admin management, subjects, themes, topics, and curriculum endpoints.
"""

import pytest
import json


class TestAdminRoutes:
    """Tests for admin management endpoints."""
    
    def test_get_admins_returns_list(self, client, sample_admin):
        """Test GET /app-admins/ returns list of admins."""
        response = client.get('/app-admins/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1
    
    def test_post_admin_with_valid_data(self, client):
        """Test POST /app-admins/ creates new admin."""
        payload = {
            "username": "newadmin",
            "email": "newadmin@testora.test",
            "password": "password123"
        }
        
        response = client.post(
            '/app-admins/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['email'] == payload['email']
    
    def test_post_admin_duplicate_email(self, client, sample_admin):
        """Test POST /app-admins/ with existing email returns error."""
        payload = {
            "username": "duplicate",
            "email": sample_admin.email,
            "password": "password123"
        }
        
        response = client.post(
            '/app-admins/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'already exists' in data['message'].lower()
    
    def test_post_admin_missing_username(self, client):
        """Test POST /app-admins/ without username returns validation error."""
        payload = {
            "email": "test@testora.test",
            "password": "password123"
        }
        
        response = client.post(
            '/app-admins/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_admin_missing_email(self, client):
        """Test POST /app-admins/ without email returns validation error."""
        payload = {
            "username": "testadmin",
            "password": "password123"
        }
        
        response = client.post(
            '/app-admins/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_admin_missing_password(self, client):
        """Test POST /app-admins/ without password returns validation error."""
        payload = {
            "username": "testadmin",
            "email": "test@testora.test"
        }
        
        response = client.post(
            '/app-admins/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_admin_authenticate_valid_credentials(self, client, sample_admin):
        """Test POST /app-admins/authenticate/ with valid credentials."""
        payload = {
            "email": sample_admin.email,
            "password": "password123"
        }
        
        response = client.post(
            '/app-admins/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'auth_token' in data['data']
        assert 'user' in data['data']
    
    def test_post_admin_authenticate_invalid_email(self, client):
        """Test POST /app-admins/authenticate/ with invalid email returns 401."""
        payload = {
            "email": "nonexistent@testora.test",
            "password": "password123"
        }
        
        response = client.post(
            '/app-admins/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_post_admin_authenticate_wrong_password(self, client, sample_admin):
        """Test POST /app-admins/authenticate/ with wrong password returns 401."""
        payload = {
            "email": sample_admin.email,
            "password": "wrongpassword"
        }
        
        response = client.post(
            '/app-admins/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401


class TestCurriculumRoutes:
    """Tests for curriculum endpoints."""
    
    def test_get_curriculums_returns_list(self, client):
        """Test GET /curriculum/ returns available curriculums."""
        response = client.get('/curriculum/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) > 0
        assert data['data'][0]['name'] == 'bece'


class TestSubjectRoutes:
    """Tests for subject management endpoints."""
    
    def test_get_subjects_returns_list_with_themes_topics(
        self, client, sample_subject, sample_theme, sample_topic
    ):
        """Test GET /subjects/ returns subjects with nested themes and topics."""
        response = client.get('/subjects/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1
        
        # Check nested structure
        subject = data['data'][0]
        assert 'themes' in subject
    
    def test_get_subjects_by_curriculum(self, client, sample_subject):
        """Test GET /subjects/<curriculum>/ returns subjects for curriculum."""
        response = client.get('/subjects/bece/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_post_subjects_with_valid_data(self, client):
        """Test POST /subjects/ creates new subjects."""
        payload = {
            "data": [
                {
                    "name": "New Subject",
                    "short_name": "New Sub",
                    "curriculum": "bece",
                    "is_premium": False,
                    "max_duration": 60
                }
            ]
        }
        
        response = client.post(
            '/subjects/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['data'], list)
        assert len(data['data']) == 1
    
    def test_post_subjects_invalid_curriculum(self, client):
        """Test POST /subjects/ with invalid curriculum returns error."""
        payload = {
            "data": [
                {
                    "name": "New Subject",
                    "short_name": "New Sub",
                    "curriculum": "invalid",
                    "is_premium": False,
                    "max_duration": 60
                }
            ]
        }
        
        response = client.post(
            '/subjects/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_put_subject_with_valid_data(self, client, sample_subject):
        """Test PUT /subjects/<id>/ updates subject."""
        payload = {
            "data": {
                "name": "Updated Math",
                "short_name": "UMath",
                "curriculum": "bece"
            }
        }
        
        response = client.put(
            f'/subjects/{sample_subject.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['name'] == "Updated Math"
    
    def test_put_subject_nonexistent_id(self, client):
        """Test PUT /subjects/<id>/ with nonexistent ID returns 404."""
        payload = {
            "data": {
                "name": "Updated Math",
                "short_name": "UMath",
                "curriculum": "bece"
            }
        }
        
        response = client.put(
            '/subjects/99999/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 404
    
    def test_delete_subject_existing_id(self, client, sample_subject):
        """Test DELETE /subjects/<id>/ deletes subject."""
        response = client.delete(f'/subjects/{sample_subject.id}/')
        
        assert response.status_code == 200
    
    def test_delete_subject_nonexistent_id(self, client):
        """Test DELETE /subjects/<id>/ with nonexistent ID returns 404."""
        response = client.delete('/subjects/99999/')
        
        assert response.status_code == 404
    
    def test_get_subject_topics(self, client, sample_subject, sample_topic):
        """Test GET /subjects/<id>/topics returns topics for subject."""
        response = client.get(f'/subjects/{sample_subject.id}/topics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)


class TestThemeRoutes:
    """Tests for theme management endpoints."""
    
    def test_get_themes_returns_list(self, client, sample_theme):
        """Test GET /themes/ returns list of themes."""
        response = client.get('/themes/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1
    
    def test_post_themes_with_valid_data(self, client, sample_subject):
        """Test POST /themes/ creates new themes."""
        payload = {
            "data": [
                {
                    "name": "New Theme",
                    "short_name": "NT",
                    "subject_id": sample_subject.id
                }
            ]
        }
        
        response = client.post(
            '/themes/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['data'], list)
        assert len(data['data']) == 1
    
    def test_post_themes_missing_subject_id(self, client):
        """Test POST /themes/ without subject_id returns validation error."""
        payload = {
            "data": [
                {
                    "name": "New Theme",
                    "short_name": "NT"
                }
            ]
        }
        
        response = client.post(
            '/themes/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_put_theme_with_valid_data(self, client, sample_theme, sample_subject):
        """Test PUT /themes/<id>/ updates theme."""
        payload = {
            "data": {
                "name": "Updated Theme",
                "short_name": "UT",
                "subject_id": sample_subject.id
            }
        }
        
        response = client.put(
            f'/themes/{sample_theme.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['name'] == "Updated Theme"
    
    def test_put_theme_nonexistent_id(self, client, sample_subject):
        """Test PUT /themes/<id>/ with nonexistent ID returns 404."""
        payload = {
            "data": {
                "name": "Updated Theme",
                "short_name": "UT",
                "subject_id": sample_subject.id
            }
        }
        
        response = client.put(
            '/themes/99999/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 404
    
    def test_delete_theme_existing_id(self, client, sample_theme):
        """Test DELETE /themes/<id>/ deletes theme."""
        response = client.delete(f'/themes/{sample_theme.id}/')
        
        assert response.status_code == 200
    
    def test_delete_theme_nonexistent_id(self, client):
        """Test DELETE /themes/<id>/ with nonexistent ID returns 404."""
        response = client.delete('/themes/99999/')
        
        assert response.status_code == 404


class TestTopicRoutes:
    """Tests for topic management endpoints."""
    
    def test_get_topics_returns_list(self, client, sample_topic):
        """Test GET /topics/ returns list of topics."""
        response = client.get('/topics/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1
    
    def test_post_topics_with_valid_data(self, client, sample_subject, sample_theme):
        """Test POST /topics/ creates new topics."""
        payload = {
            "data": [
                {
                    "name": "New Topic",
                    "short_name": "NTop",
                    "subject_id": sample_subject.id,
                    "theme_id": sample_theme.id
                }
            ]
        }
        
        response = client.post(
            '/topics/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['data'], list)
        assert len(data['data']) == 1
    
    def test_post_topics_missing_subject_id(self, client, sample_theme):
        """Test POST /topics/ without subject_id returns validation error."""
        payload = {
            "data": [
                {
                    "name": "New Topic",
                    "short_name": "NTop",
                    "theme_id": sample_theme.id
                }
            ]
        }
        
        response = client.post(
            '/topics/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_topics_missing_theme_id(self, client, sample_subject):
        """Test POST /topics/ without theme_id returns validation error."""
        payload = {
            "data": [
                {
                    "name": "New Topic",
                    "short_name": "NTop",
                    "subject_id": sample_subject.id
                }
            ]
        }
        
        response = client.post(
            '/topics/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_put_topic_with_valid_data(self, client, sample_topic, sample_subject):
        """Test PUT /topics/<id>/ updates topic."""
        payload = {
            "data": {
                "name": "Updated Topic",
                "short_name": "UTopic",
                "subject_id": sample_subject.id
            }
        }
        
        response = client.put(
            f'/topics/{sample_topic.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['name'] == "Updated Topic"
    
    def test_put_topic_nonexistent_id(self, client, sample_subject):
        """Test PUT /topics/<id>/ with nonexistent ID returns 404."""
        payload = {
            "data": {
                "name": "Updated Topic",
                "short_name": "UTopic",
                "subject_id": sample_subject.id
            }
        }
        
        response = client.put(
            '/topics/99999/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 404
    
    def test_delete_topic_existing_id(self, client, sample_topic):
        """Test DELETE /topics/<id>/ deletes topic."""
        response = client.delete(f'/topics/{sample_topic.id}/')
        
        assert response.status_code == 200
    
    def test_delete_topic_nonexistent_id(self, client):
        """Test DELETE /topics/<id>/ with nonexistent ID returns 404."""
        response = client.delete('/topics/99999/')
        
        assert response.status_code == 404
