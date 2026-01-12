"""
Comprehensive tests for student routes (app/student/routes.py)
Tests cover student registration, authentication, approval, batch management, and analytics.
"""

import pytest
import json


class TestStudentRegistration:
    """Tests for POST /students/register/ endpoint."""
    
    def test_post_student_register_with_valid_data(
        self, client, sample_school, mock_mailer
    ):
        """Test student registration with valid data."""
        payload = {
            "first_name": "New",
            "surname": "Student",
            "other_names": "Test",
            "email": "newstudent@test.com",
            "password": "password123",
            "school_code": sample_school.code
        }
        
        response = client.post(
            '/students/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        assert mock_mailer.send_email.called
    
    def test_post_student_register_duplicate_email(
        self, client, sample_student, sample_school
    ):
        """Test student registration with existing email returns error."""
        payload = {
            "first_name": "Duplicate",
            "surname": "Student",
            "email": sample_student.email,
            "password": "password123",
            "school_code": sample_school.code
        }
        
        response = client.post(
            '/students/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_post_student_register_invalid_school_code(self, client):
        """Test student registration with invalid school code returns 400."""
        payload = {
            "first_name": "New",
            "surname": "Student",
            "email": "newstudent@test.com",
            "password": "password123",
            "school_code": "INVALID"
        }
        
        response = client.post(
            '/students/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestStudentAuthentication:
    """Tests for POST /students/authenticate/ endpoint."""
    
    def test_post_student_authenticate_valid_credentials(
        self, client, sample_student
    ):
        """Test student authentication with valid credentials."""
        payload = {
            "email": sample_student.email,
            "password": "password123"
        }
        
        response = client.post(
            '/students/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'auth_token' in data['data']
        assert 'user' in data['data']
        assert 'school' in data['data']
        assert data['data']['user_type'] == 'student'
    
    def test_post_student_authenticate_unapproved(
        self, client, unapproved_student
    ):
        """Test unapproved student cannot authenticate."""
        payload = {
            "email": unapproved_student.email,
            "password": "password123"
        }
        
        response = client.post(
            '/students/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 403
    
    def test_post_student_authenticate_wrong_password(self, client, sample_student):
        """Test student authentication with wrong password returns 401."""
        payload = {
            "email": sample_student.email,
            "password": "wrongpassword"
        }
        
        response = client.post(
            '/students/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401


class TestStudentApproval:
    """Tests for POST /students/approve/ and /students/unapprove/ endpoints."""
    
    def test_post_students_approve(
        self, client, school_admin_headers, unapproved_student
    ):
        """Test student approval by school admin."""
        payload = {
            "student_ids": [unapproved_student.id]
        }
        
        response = client.post(
            '/students/approve/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_post_students_unapprove(
        self, client, school_admin_headers, sample_student
    ):
        """Test student unapproval by school admin."""
        payload = {
            "student_ids": [sample_student.id]
        }
        
        response = client.post(
            '/students/unapprove/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200


class TestStudentList:
    """Tests for GET /students/ endpoint."""
    
    def test_get_students_with_school_admin_auth(
        self, client, school_admin_headers, sample_student
    ):
        """Test GET /students/ with school admin auth returns student list."""
        response = client.get('/students/', headers=school_admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_students_without_auth(self, client):
        """Test GET /students/ without auth returns 401."""
        response = client.get('/students/')
        
        assert response.status_code == 401


class TestStudentDetails:
    """Tests for GET /students/<id>/ endpoint."""
    
    def test_get_student_details(
        self, client, student_headers, sample_student
    ):
        """Test GET /students/<id>/ returns student details."""
        response = client.get(
            f'/students/{sample_student.id}/',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['id'] == sample_student.id
    
    def test_get_student_details_nonexistent(self, client, student_headers):
        """Test GET /students/<id>/ with nonexistent ID returns 404."""
        response = client.get('/students/99999/', headers=student_headers)
        
        assert response.status_code == 404


class TestEndSession:
    """Tests for POST /students/end-session/ endpoint."""
    
    def test_post_end_session_as_student(self, client, student_headers, sample_student):
        """Test POST /students/end-session/ records session."""
        payload = {
            "data": [
                {
                    "student_id": sample_student.id,
                    "date": "2024-01-15",
                    "duration": 3600000  # 1 hour in milliseconds
                }
            ]
        }
        
        response = client.post(
            '/students/end-session/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 200


class TestBatchManagement:
    """Tests for batch management endpoints."""
    
    def test_post_batches_create(
        self, client, school_admin_headers, sample_student
    ):
        """Test POST /batches/ creates new batch."""
        payload = {
            "data": {
                "batch_name": "Form 4B",
                "curriculum": "bece",
                "students": [sample_student.id],
                "staff": []
            }
        }
        
        response = client.post(
            '/batches/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['batch_name'] == "Form 4B"
    
    def test_put_batches_update(
        self, client, school_admin_headers, sample_batch, sample_student
    ):
        """Test PUT /batches/<id>/ updates batch."""
        payload = {
            "data": {
                "batch_name": "Updated Batch",
                "curriculum": "bece",
                "students": [sample_student.id],
                "staff": []
            }
        }
        
        response = client.put(
            f'/batches/{sample_batch.id}/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_batches(self, client, school_admin_headers, sample_batch):
        """Test GET /batches/ returns batch list."""
        response = client.get('/batches/', headers=school_admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)


class TestStudentLevels:
    """Tests for GET /students/subject-levels/ endpoint."""
    
    def test_get_subject_levels_as_student(
        self, client, student_headers, sample_student, student_subject_level
    ):
        """Test GET /students/subject-levels/ as student."""
        response = client.get(
            '/students/subject-levels/',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_get_subject_levels_as_staff(
        self, client, staff_headers, sample_student
    ):
        """Test GET /students/subject-levels/ as staff with student_id."""
        response = client.get(
            f'/students/subject-levels/?student_id={sample_student.id}',
            headers=staff_headers
        )
        
        assert response.status_code == 200


class TestStudentDashboard:
    """Tests for student dashboard analytics endpoints."""
    
    def test_get_total_tests(self, client, student_headers, sample_student):
        """Test GET /students/dashboard/total-tests/ returns test count."""
        response = client.get(
            '/students/dashboard/total-tests/',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tests_completed' in data['data']
    
    def test_get_line_chart(
        self, client, student_headers, sample_student, sample_batch
    ):
        """Test GET /students/dashboard/line-chart/ returns chart data."""
        response = client.get(
            '/students/dashboard/line-chart/',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['data'], list)
    
    def test_get_pie_chart(
        self, client, student_headers, sample_student, sample_batch
    ):
        """Test GET /students/dashboard/pie-chart/ returns chart data."""
        response = client.get(
            '/students/dashboard/pie-chart/',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['data'], list)
    
    def test_get_bar_chart(
        self, client, student_headers, sample_student, sample_batch
    ):
        """Test GET /students/dashboard/bar-chart/ returns chart data."""
        response = client.get(
            '/students/dashboard/bar-chart/',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['data'], list)
    
    def test_get_student_averages(
        self, client, student_headers, sample_student, sample_subject
    ):
        """Test GET /students/averages/ returns student performance data."""
        response = client.get(
            f'/students/averages/?student_id={sample_student.id}',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['data'], list)
    
    def test_get_student_averages_with_filters(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /students/averages/ with batch and subject filters."""
        response = client.get(
            f'/students/averages/?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
