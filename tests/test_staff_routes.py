"""
Comprehensive tests for staff routes (app/staff/routes.py)
Tests cover staff registration, authentication, approval, and management.
"""

import pytest
import json


class TestSchoolAdminRegistration:
    """Tests for POST /school-admin/register/ endpoint."""
    
    def test_post_school_admin_register_with_valid_data(self, client, mock_mailer):
        """Test school admin registration with valid data."""
        payload = {
            "school": {
                "name": "New Test School",
                "location": "Test City"
            },
            "school_admin": {
                "first_name": "Admin",
                "surname": "User",
                "other_names": "Test",
                "email": "admin@newschool.test",
                "password": "password123",
                "school_code": "will_be_removed"
            }
        }
        
        response = client.post(
            '/school-admin/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        assert mock_mailer.send_email.called
    
    def test_post_school_admin_register_duplicate_email(
        self, client, sample_school_admin
    ):
        """Test school admin registration with existing email returns error."""
        payload = {
            "school": {
                "name": "Another School",
                "location": "Test City"
            },
            "school_admin": {
                "first_name": "Admin",
                "surname": "User",
                "other_names": "Test",
                "email": sample_school_admin.email,
                "password": "password123",
                "school_code": "will_be_removed"
            }
        }
        
        response = client.post(
            '/school-admin/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_post_school_admin_register_missing_school_data(self, client):
        """Test school admin registration without school data returns validation error."""
        payload = {
            "school_admin": {
                "first_name": "Admin",
                "surname": "User",
                "email": "admin@test.com",
                "password": "password123"
            }
        }
        
        response = client.post(
            '/school-admin/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_school_admin_register_missing_admin_email(self, client):
        """Test school admin registration without admin email returns validation error."""
        payload = {
            "school": {
                "name": "Test School",
                "location": "Test City"
            },
            "school_admin": {
                "first_name": "Admin",
                "surname": "User",
                "password": "password123"
            }
        }
        
        response = client.post(
            '/school-admin/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422


class TestStaffRegistration:
    """Tests for POST /staff/register/ endpoint."""
    
    def test_post_staff_register_with_valid_data(
        self, client, sample_school, mock_mailer
    ):
        """Test staff registration with valid data."""
        payload = {
            "first_name": "New",
            "surname": "Teacher",
            "other_names": "Test",
            "email": "newteacher@test.com",
            "password": "password123",
            "school_code": sample_school.code
        }
        
        response = client.post(
            '/staff/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        assert mock_mailer.send_email.called
    
    def test_post_staff_register_duplicate_email(self, client, sample_staff, sample_school):
        """Test staff registration with existing email returns error."""
        payload = {
            "first_name": "New",
            "surname": "Teacher",
            "email": sample_staff.email,
            "password": "password123",
            "school_code": sample_school.code
        }
        
        response = client.post(
            '/staff/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_post_staff_register_invalid_school_code(self, client):
        """Test staff registration with invalid school code returns 401."""
        payload = {
            "first_name": "New",
            "surname": "Teacher",
            "email": "newteacher@test.com",
            "password": "password123",
            "school_code": "INVALID"
        }
        
        response = client.post(
            '/staff/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_post_staff_register_missing_school_code(self, client):
        """Test staff registration without school code returns validation error."""
        payload = {
            "first_name": "New",
            "surname": "Teacher",
            "email": "newteacher@test.com",
            "password": "password123"
        }
        
        response = client.post(
            '/staff/register/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422


class TestStaffAuthentication:
    """Tests for POST /staff/authenticate/ endpoint."""
    
    def test_post_staff_authenticate_valid_credentials(self, client, sample_staff):
        """Test staff authentication with valid credentials."""
        payload = {
            "email": sample_staff.email,
            "password": "password123"
        }
        
        response = client.post(
            '/staff/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'auth_token' in data['data']
        assert 'user' in data['data']
        assert 'school' in data['data']
        assert data['data']['user_type'] == 'staff'
    
    def test_post_staff_authenticate_school_admin(self, client, sample_school_admin):
        """Test school admin authentication returns school_admin type."""
        payload = {
            "email": sample_school_admin.email,
            "password": "password123"
        }
        
        response = client.post(
            '/staff/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['user_type'] == 'school_admin'
        # School admin should see school code
        assert 'code' in data['data']['school']
    
    def test_post_staff_authenticate_regular_staff_no_code(
        self, client, sample_staff
    ):
        """Test regular staff doesn't see school code in response."""
        payload = {
            "email": sample_staff.email,
            "password": "password123"
        }
        
        response = client.post(
            '/staff/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Regular staff shouldn't see school code
        assert 'code' not in data['data']['school']
    
    def test_post_staff_authenticate_unapproved_staff(
        self, client, unapproved_staff
    ):
        """Test unapproved staff cannot authenticate."""
        payload = {
            "email": unapproved_staff.email,
            "password": "password123"
        }
        
        response = client.post(
            '/staff/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 403
    
    def test_post_staff_authenticate_wrong_password(self, client, sample_staff):
        """Test staff authentication with wrong password returns 401."""
        payload = {
            "email": sample_staff.email,
            "password": "wrongpassword"
        }
        
        response = client.post(
            '/staff/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_post_staff_authenticate_nonexistent_email(self, client):
        """Test staff authentication with nonexistent email returns 401."""
        payload = {
            "email": "nonexistent@test.com",
            "password": "password123"
        }
        
        response = client.post(
            '/staff/authenticate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401


class TestStaffApproval:
    """Tests for POST /staff/approve/ endpoint."""
    
    def test_post_staff_approve_with_school_admin_auth(
        self, client, school_admin_headers, unapproved_staff
    ):
        """Test staff approval by school admin."""
        payload = {
            "staff_ids": [unapproved_staff.id]
        }
        
        response = client.post(
            '/staff/approve/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_post_staff_approve_without_auth(self, client, unapproved_staff):
        """Test staff approval without auth returns 401."""
        payload = {
            "staff_ids": [unapproved_staff.id]
        }
        
        response = client.post(
            '/staff/approve/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_post_staff_approve_with_staff_auth(
        self, client, staff_headers, unapproved_staff
    ):
        """Test staff approval by regular staff returns 403."""
        payload = {
            "staff_ids": [unapproved_staff.id]
        }
        
        response = client.post(
            '/staff/approve/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=staff_headers
        )
        
        assert response.status_code == 403
    
    def test_post_staff_approve_multiple_staff(
        self, client, school_admin_headers, unapproved_staff
    ):
        """Test approving multiple staff members."""
        payload = {
            "staff_ids": [unapproved_staff.id, 999]
        }
        
        response = client.post(
            '/staff/approve/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200


class TestStaffUnapproval:
    """Tests for POST /staff/unapprove/ endpoint."""
    
    def test_post_staff_unapprove_with_school_admin_auth(
        self, client, school_admin_headers, sample_staff
    ):
        """Test staff unapproval by school admin."""
        payload = {
            "staff_ids": [sample_staff.id]
        }
        
        response = client.post(
            '/staff/unapprove/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_post_staff_unapprove_without_auth(self, client, sample_staff):
        """Test staff unapproval without auth returns 401."""
        payload = {
            "staff_ids": [sample_staff.id]
        }
        
        response = client.post(
            '/staff/unapprove/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401


class TestStaffList:
    """Tests for GET /staff/ endpoint."""
    
    def test_get_staff_list_with_school_admin_auth(
        self, client, school_admin_headers, sample_staff
    ):
        """Test GET /staff/ with school admin auth returns staff list."""
        response = client.get('/staff/', headers=school_admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_staff_list_without_auth(self, client):
        """Test GET /staff/ without auth returns 401."""
        response = client.get('/staff/')
        
        assert response.status_code == 401
    
    def test_get_staff_list_with_staff_auth(self, client, staff_headers):
        """Test GET /staff/ with regular staff auth returns 403."""
        response = client.get('/staff/', headers=staff_headers)
        
        assert response.status_code == 403


class TestStaffDetails:
    """Tests for GET /staff/<id>/ endpoint."""
    
    def test_get_staff_details_with_any_auth(
        self, client, student_headers, sample_staff
    ):
        """Test GET /staff/<id>/ with any authenticated user."""
        response = client.get(
            f'/staff/{sample_staff.id}/',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert data['data']['id'] == sample_staff.id
    
    def test_get_staff_details_nonexistent_id(self, client, student_headers):
        """Test GET /staff/<id>/ with nonexistent ID returns 404."""
        response = client.get('/staff/99999/', headers=student_headers)
        
        assert response.status_code == 404
    
    def test_get_staff_details_without_auth(self, client, sample_staff):
        """Test GET /staff/<id>/ without auth returns 401."""
        response = client.get(f'/staff/{sample_staff.id}/')
        
        assert response.status_code == 401


class TestEditStaff:
    """Tests for PUT /staff/<id>/ endpoint."""
    
    def test_put_staff_details_with_school_admin_auth(
        self, client, school_admin_headers, sample_staff
    ):
        """Test PUT /staff/<id>/ updates staff details."""
        payload = {
            "data": {
                "first_name": "Updated",
                "surname": "Name",
                "email": sample_staff.email,
                "is_admin": False,
                "subjects": []
            }
        }
        
        response = client.put(
            f'/staff/{sample_staff.id}/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['first_name'] == "Updated"
    
    def test_put_staff_details_nonexistent_id(
        self, client, school_admin_headers
    ):
        """Test PUT /staff/<id>/ with nonexistent ID returns 404."""
        payload = {
            "data": {
                "first_name": "Updated",
                "surname": "Name",
                "email": "test@test.com",
                "subjects": []
            }
        }
        
        response = client.put(
            '/staff/99999/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 404
    
    def test_put_staff_details_without_auth(self, client, sample_staff):
        """Test PUT /staff/<id>/ without auth returns 401."""
        payload = {
            "data": {
                "first_name": "Updated",
                "subjects": []
            }
        }
        
        response = client.put(
            f'/staff/{sample_staff.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401


class TestDashboardGeneral:
    """Tests for GET /school-admin/dashboard-general/ endpoint."""
    
    def test_get_dashboard_general_with_school_admin_auth(
        self, client, school_admin_headers, sample_student, sample_staff
    ):
        """Test GET /school-admin/dashboard-general/ returns dashboard data."""
        response = client.get(
            '/school-admin/dashboard-general/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert 'total_students' in data['data']
        assert 'total_staff' in data['data']
        assert 'total_batches' in data['data']
        assert 'total_tests' in data['data']
        assert 'package_information' in data['data']
    
    def test_get_dashboard_general_without_auth(self, client):
        """Test GET /school-admin/dashboard-general/ without auth returns 401."""
        response = client.get('/school-admin/dashboard-general/')
        
        assert response.status_code == 401
    
    def test_get_dashboard_general_with_staff_auth(self, client, staff_headers):
        """Test GET /school-admin/dashboard-general/ with staff auth returns 403."""
        response = client.get(
            '/school-admin/dashboard-general/',
            headers=staff_headers
        )
        
        assert response.status_code == 403
    
    def test_get_dashboard_general_package_info_structure(
        self, client, school_admin_headers
    ):
        """Test dashboard returns proper package information structure."""
        response = client.get(
            '/school-admin/dashboard-general/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        package_info = data['data']['package_information']
        assert 'subscription_package' in package_info
        assert 'subscription_expiry' in package_info
        assert 'subscription_description' in package_info
