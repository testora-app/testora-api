"""
Comprehensive tests for notifications routes (app/notifications/routes.py)
Tests cover notification management and device ID registration.
"""

import pytest
import json


class TestNotificationsRoutes:
    """Tests for GET /notifications/ endpoint."""
    
    def test_get_notifications_with_student_auth(
        self, client, student_headers, sample_recipient, sample_notification
    ):
        """Test GET /notifications/ with student auth returns notifications."""
        response = client.get('/notifications/', headers=student_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_notifications_with_staff_auth(
        self, client, staff_headers, sample_recipient
    ):
        """Test GET /notifications/ with staff auth returns notifications."""
        response = client.get('/notifications/', headers=staff_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_notifications_with_school_admin_auth(
        self, client, school_admin_headers
    ):
        """Test GET /notifications/ with school admin auth returns notifications."""
        response = client.get('/notifications/', headers=school_admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_get_notifications_without_auth(self, client):
        """Test GET /notifications/ without auth returns 401."""
        response = client.get('/notifications/')
        
        assert response.status_code == 401
    
    def test_get_notifications_with_invalid_token(self, client):
        """Test GET /notifications/ with invalid token returns 401."""
        headers = {'Authorization': 'Bearer invalid.token'}
        response = client.get('/notifications/', headers=headers)
        
        assert response.status_code == 401
    
    def test_get_notifications_empty_for_user_without_recipient(
        self, client, student_headers
    ):
        """Test GET /notifications/ returns empty list for user without recipient."""
        response = client.get('/notifications/', headers=student_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data'] == []


class TestReadNotificationsRoute:
    """Tests for PUT /notifications/read/ endpoint."""
    
    def test_put_read_notifications_with_valid_data(
        self, client, student_headers, sample_notification
    ):
        """Test PUT /notifications/read/ marks notifications as read."""
        payload = {
            "data": {
                "notification_ids": [sample_notification.id]
            }
        }
        
        response = client.put(
            '/notifications/read/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_put_read_notifications_multiple_ids(
        self, client, student_headers, sample_notification
    ):
        """Test PUT /notifications/read/ with multiple notification IDs."""
        payload = {
            "data": {
                "notification_ids": [sample_notification.id, 999]
            }
        }
        
        response = client.put(
            '/notifications/read/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_put_read_notifications_without_auth(self, client):
        """Test PUT /notifications/read/ without auth returns 401."""
        payload = {
            "data": {
                "notification_ids": [1]
            }
        }
        
        response = client.put(
            '/notifications/read/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_put_read_notifications_missing_notification_ids(
        self, client, student_headers
    ):
        """Test PUT /notifications/read/ without notification_ids returns validation error."""
        payload = {
            "data": {}
        }
        
        response = client.put(
            '/notifications/read/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 422
    
    def test_put_read_notifications_empty_list(self, client, student_headers):
        """Test PUT /notifications/read/ with empty list."""
        payload = {
            "data": {
                "notification_ids": []
            }
        }
        
        response = client.put(
            '/notifications/read/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 200


class TestDeviceIDsRoute:
    """Tests for POST /device-ids/ endpoint."""
    
    def test_post_device_ids_creates_new_recipient(
        self, client, student_headers, mock_pusher
    ):
        """Test POST /device-ids/ creates new recipient and sends welcome notification."""
        payload = {
            "data": {
                "device_ids": ["device-id-123", "device-id-456"]
            }
        }
        
        response = client.post(
            '/device-ids/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'data' in data
        assert 'device_ids' in data['data']
        
        # Verify notification was sent
        assert mock_pusher.notify_devices.called
    
    def test_post_device_ids_updates_existing_recipient(
        self, client, student_headers, sample_recipient, mock_pusher
    ):
        """Test POST /device-ids/ updates existing recipient's device IDs."""
        payload = {
            "data": {
                "device_ids": ["new-device-id-1", "new-device-id-2"]
            }
        }
        
        response = client.post(
            '/device-ids/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'device_ids' in data['data']
        
        # Verify notification was sent
        assert mock_pusher.notify_devices.called
    
    def test_post_device_ids_without_auth(self, client):
        """Test POST /device-ids/ without auth returns 401."""
        payload = {
            "data": {
                "device_ids": ["device-id-123"]
            }
        }
        
        response = client.post(
            '/device-ids/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_post_device_ids_missing_device_ids(self, client, student_headers):
        """Test POST /device-ids/ without device_ids returns validation error."""
        payload = {
            "data": {}
        }
        
        response = client.post(
            '/device-ids/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 422
    
    def test_post_device_ids_empty_list(self, client, student_headers, mock_pusher):
        """Test POST /device-ids/ with empty device IDs list."""
        payload = {
            "data": {
                "device_ids": []
            }
        }
        
        response = client.post(
            '/device-ids/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=student_headers
        )
        
        assert response.status_code == 201
    
    def test_post_device_ids_with_staff_auth(
        self, client, staff_headers, mock_pusher
    ):
        """Test POST /device-ids/ works with staff authentication."""
        payload = {
            "data": {
                "device_ids": ["staff-device-id"]
            }
        }
        
        response = client.post(
            '/device-ids/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=staff_headers
        )
        
        assert response.status_code == 201
    
    def test_post_device_ids_with_school_admin_auth(
        self, client, school_admin_headers, mock_pusher
    ):
        """Test POST /device-ids/ works with school admin authentication."""
        payload = {
            "data": {
                "device_ids": ["admin-device-id"]
            }
        }
        
        response = client.post(
            '/device-ids/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 201


class TestTestNotificationsRoute:
    """Tests for GET /test-notifications/ endpoint."""
    
    def test_get_test_notifications_sends_to_specific_recipients(
        self, client, sample_recipient, mock_pusher
    ):
        """Test GET /test-notifications/ sends test notifications."""
        response = client.get('/test-notifications/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status_code'] == 200
    
    def test_get_test_notifications_with_all_param(
        self, client, sample_recipient, mock_pusher
    ):
        """Test GET /test-notifications/?all=true sends to all recipients."""
        response = client.get('/test-notifications/?all=true')
        
        assert response.status_code == 200
    
    def test_get_test_notifications_custom_title(self, client, mock_pusher):
        """Test GET /test-notifications/ with custom title."""
        response = client.get('/test-notifications/?title=Custom Title')
        
        assert response.status_code == 200
    
    def test_get_test_notifications_custom_message(self, client, mock_pusher):
        """Test GET /test-notifications/ with custom message."""
        response = client.get('/test-notifications/?message=Custom Message')
        
        assert response.status_code == 200
    
    def test_get_test_notifications_no_auth_required(self, client, mock_pusher):
        """Test GET /test-notifications/ doesn't require authentication."""
        response = client.get('/test-notifications/')
        
        # Should work without authentication
        assert response.status_code == 200
    
    def test_get_test_notifications_with_all_params(self, client, mock_pusher):
        """Test GET /test-notifications/ with all parameters."""
        response = client.get(
            '/test-notifications/?all=true&title=Test&message=Test Message'
        )
        
        assert response.status_code == 200
