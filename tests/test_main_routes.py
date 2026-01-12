"""
Comprehensive tests for main routes (app/routes.py)
Tests cover: /, /contact-us/, /account/reset-password/, /account/change-password/
"""

import pytest
import json
import jwt
from datetime import datetime, timezone, timedelta


class TestIndexRoute:
    """Tests for GET / endpoint."""
    
    def test_get_index_returns_success(self, client):
        """Test that index route returns success message."""
        response = client.get('/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert 'Testora' in data['message']
    
    def test_get_index_no_auth_required(self, client):
        """Test that index route doesn't require authentication."""
        response = client.get('/')
        assert response.status_code == 200


class TestContactUsRoute:
    """Tests for POST /contact-us/ endpoint."""
    
    def test_post_contact_us_with_valid_data(self, client, mock_mailer):
        """Test contact us with valid data sends emails."""
        payload = {
            "data": {
                "name": "John Doe",
                "email": "john@example.com",
                "message": "I need help with my account"
            }
        }
        
        response = client.post(
            '/contact-us/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status_code'] == 200
        
        # Verify emails were sent
        assert mock_mailer.send_email.call_count == 2
    
    def test_post_contact_us_missing_name(self, client):
        """Test contact us with missing name returns validation error."""
        payload = {
            "data": {
                "email": "john@example.com",
                "message": "I need help"
            }
        }
        
        response = client.post(
            '/contact-us/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_contact_us_missing_email(self, client):
        """Test contact us with missing email returns validation error."""
        payload = {
            "data": {
                "name": "John Doe",
                "message": "I need help"
            }
        }
        
        response = client.post(
            '/contact-us/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_contact_us_missing_message(self, client):
        """Test contact us with missing message returns validation error."""
        payload = {
            "data": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        }
        
        response = client.post(
            '/contact-us/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_contact_us_invalid_email_format(self, client):
        """Test contact us with invalid email format returns validation error."""
        payload = {
            "data": {
                "name": "John Doe",
                "email": "invalid-email",
                "message": "I need help"
            }
        }
        
        response = client.post(
            '/contact-us/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_contact_us_empty_name(self, client):
        """Test contact us with empty name returns validation error."""
        payload = {
            "data": {
                "name": "",
                "email": "john@example.com",
                "message": "I need help"
            }
        }
        
        response = client.post(
            '/contact-us/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_contact_us_empty_message(self, client):
        """Test contact us with empty message returns validation error."""
        payload = {
            "data": {
                "name": "John Doe",
                "email": "john@example.com",
                "message": ""
            }
        }
        
        response = client.post(
            '/contact-us/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422


class TestResetPasswordRoute:
    """Tests for POST /account/reset-password/ endpoint."""
    
    def test_post_reset_password_student_valid_email(
        self, client, sample_student, mock_mailer
    ):
        """Test reset password for student with valid email sends email."""
        payload = {
            "data": {
                "email": sample_student.email
            }
        }
        
        response = client.post(
            '/account/reset-password/?user_type=student',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status_code'] == 200
        
        # Verify email was sent
        assert mock_mailer.send_email.called
    
    def test_post_reset_password_staff_valid_email(
        self, client, sample_staff, mock_mailer
    ):
        """Test reset password for staff with valid email sends email."""
        payload = {
            "data": {
                "email": sample_staff.email
            }
        }
        
        response = client.post(
            '/account/reset-password/?user_type=staff',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status_code'] == 200
        
        # Verify email was sent
        assert mock_mailer.send_email.called
    
    def test_post_reset_password_nonexistent_email(self, client, mock_mailer):
        """Test reset password with nonexistent email still returns success."""
        payload = {
            "data": {
                "email": "nonexistent@example.com"
            }
        }
        
        response = client.post(
            '/account/reset-password/?user_type=student',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should return success even if email doesn't exist (security best practice)
        assert response.status_code == 200
    
    def test_post_reset_password_missing_user_type(self, client):
        """Test reset password without user_type parameter returns error."""
        payload = {
            "data": {
                "email": "test@example.com"
            }
        }
        
        response = client.post(
            '/account/reset-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'user_type' in data['message']
    
    def test_post_reset_password_invalid_user_type(self, client):
        """Test reset password with invalid user_type."""
        payload = {
            "data": {
                "email": "test@example.com"
            }
        }
        
        response = client.post(
            '/account/reset-password/?user_type=invalid',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should return success (user won't exist for invalid type)
        assert response.status_code == 200
    
    def test_post_reset_password_missing_email(self, client):
        """Test reset password without email returns validation error."""
        payload = {
            "data": {}
        }
        
        response = client.post(
            '/account/reset-password/?user_type=student',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_reset_password_invalid_email_format(self, client):
        """Test reset password with invalid email format returns validation error."""
        payload = {
            "data": {
                "email": "invalid-email"
            }
        }
        
        response = client.post(
            '/account/reset-password/?user_type=student',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422


class TestChangePasswordRoute:
    """Tests for POST /account/change-password/ endpoint."""
    
    def test_post_change_password_student_valid_token(
        self, client, app, sample_student, mock_mailer
    ):
        """Test change password for student with valid confirmation token."""
        # Generate valid confirmation token
        with app.app_context():
            token = jwt.encode(
                {
                    'user_id': sample_student.id,
                    'user_type': 'student',
                    'exp': datetime.now(timezone.utc) + timedelta(hours=24)
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        
        payload = {
            "data": {
                "confirmation_code": token,
                "new_password": "NewPassword123!"
            }
        }
        
        response = client.post(
            '/account/change-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status_code'] == 200
        
        # Verify password changed email was sent
        assert mock_mailer.send_email.called
    
    def test_post_change_password_staff_valid_token(
        self, client, app, sample_staff, mock_mailer
    ):
        """Test change password for staff with valid confirmation token."""
        # Generate valid confirmation token
        with app.app_context():
            token = jwt.encode(
                {
                    'user_id': sample_staff.id,
                    'user_type': 'staff',
                    'exp': datetime.now(timezone.utc) + timedelta(hours=24)
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        
        payload = {
            "data": {
                "confirmation_code": token,
                "new_password": "NewPassword123!"
            }
        }
        
        response = client.post(
            '/account/change-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status_code'] == 200
        
        # Verify password changed email was sent
        assert mock_mailer.send_email.called
    
    def test_post_change_password_expired_token(self, client, app, sample_student):
        """Test change password with expired token returns error."""
        # Generate expired confirmation token
        with app.app_context():
            token = jwt.encode(
                {
                    'user_id': sample_student.id,
                    'user_type': 'student',
                    'exp': datetime.now(timezone.utc) - timedelta(hours=1)
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        
        payload = {
            "data": {
                "confirmation_code": token,
                "new_password": "NewPassword123!"
            }
        }
        
        response = client.post(
            '/account/change-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'expired' in data['message'].lower()
    
    def test_post_change_password_invalid_token(self, client):
        """Test change password with invalid token returns error."""
        payload = {
            "data": {
                "confirmation_code": "invalid.token.here",
                "new_password": "NewPassword123!"
            }
        }
        
        response = client.post(
            '/account/change-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'invalid' in data['message'].lower()
    
    def test_post_change_password_missing_confirmation_code(self, client):
        """Test change password without confirmation code returns validation error."""
        payload = {
            "data": {
                "new_password": "NewPassword123!"
            }
        }
        
        response = client.post(
            '/account/change-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_change_password_missing_new_password(self, client, app, sample_student):
        """Test change password without new password returns validation error."""
        # Generate valid confirmation token
        with app.app_context():
            token = jwt.encode(
                {
                    'user_id': sample_student.id,
                    'user_type': 'student',
                    'exp': datetime.now(timezone.utc) + timedelta(hours=24)
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        
        payload = {
            "data": {
                "confirmation_code": token
            }
        }
        
        response = client.post(
            '/account/change-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
    
    def test_post_change_password_nonexistent_user(self, client, app):
        """Test change password for nonexistent user."""
        # Generate valid token for nonexistent user
        with app.app_context():
            token = jwt.encode(
                {
                    'user_id': 99999,
                    'user_type': 'student',
                    'exp': datetime.now(timezone.utc) + timedelta(hours=24)
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        
        payload = {
            "data": {
                "confirmation_code": token,
                "new_password": "NewPassword123!"
            }
        }
        
        response = client.post(
            '/account/change-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should return success even if user doesn't exist
        assert response.status_code == 200
    
    def test_post_change_password_empty_new_password(self, client, app, sample_student):
        """Test change password with empty new password returns validation error."""
        # Generate valid confirmation token
        with app.app_context():
            token = jwt.encode(
                {
                    'user_id': sample_student.id,
                    'user_type': 'student',
                    'exp': datetime.now(timezone.utc) + timedelta(hours=24)
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        
        payload = {
            "data": {
                "confirmation_code": token,
                "new_password": ""
            }
        }
        
        response = client.post(
            '/account/change-password/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 422
