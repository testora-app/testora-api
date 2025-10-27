"""
Comprehensive tests for school routes (app/school/routes.py)
Tests cover school management endpoints.
"""

import pytest
import json


class TestSchoolRoutes:
    """Tests for school management endpoints."""
    
    def test_get_schools_with_admin_auth(self, client, auth_headers, sample_school):
        """Test GET /schools/ with admin authentication returns schools."""
        response = client.get('/schools/', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1
    
    def test_get_schools_without_auth(self, client, sample_school):
        """Test GET /schools/ without authentication returns 401."""
        response = client.get('/schools/')
        
        assert response.status_code == 401
    
    def test_get_schools_with_student_auth(self, client, student_headers, sample_school):
        """Test GET /schools/ with student auth returns 403 (admin only)."""
        response = client.get('/schools/', headers=student_headers)
        
        assert response.status_code == 403
    
    def test_get_schools_with_staff_auth(self, client, staff_headers, sample_school):
        """Test GET /schools/ with staff auth returns 403 (admin only)."""
        response = client.get('/schools/', headers=staff_headers)
        
        assert response.status_code == 403
    
    def test_get_schools_with_school_admin_auth(
        self, client, school_admin_headers, sample_school
    ):
        """Test GET /schools/ with school admin auth returns 403 (app admin only)."""
        response = client.get('/schools/', headers=school_admin_headers)
        
        assert response.status_code == 403
    
    def test_get_schools_with_invalid_token(self, client, sample_school):
        """Test GET /schools/ with invalid token returns 401."""
        headers = {'Authorization': 'Bearer invalid.token.here'}
        response = client.get('/schools/', headers=headers)
        
        assert response.status_code == 401
    
    def test_get_schools_with_expired_token(self, client, expired_token, sample_school):
        """Test GET /schools/ with expired token returns 401."""
        headers = {'Authorization': f'Bearer {expired_token}'}
        response = client.get('/schools/', headers=headers)
        
        assert response.status_code == 401
    
    def test_get_schools_returns_school_data_structure(
        self, client, auth_headers, sample_school
    ):
        """Test GET /schools/ returns proper school data structure."""
        response = client.get('/schools/', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        if len(data['data']) > 0:
            school = data['data'][0]
            assert 'id' in school
            assert 'name' in school
            assert 'code' in school
            assert 'location' in school
            assert 'subscription_package' in school
    
    def test_get_schools_multiple_schools(
        self, client, auth_headers, sample_school, sample_free_school
    ):
        """Test GET /schools/ returns multiple schools."""
        response = client.get('/schools/', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) >= 2
