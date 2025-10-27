"""
Comprehensive tests for subscription routes (app/subscriptions/routes.py)
Tests cover billing history, subscription creation, payment processing, and webhooks.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta


class TestBillingHistory:
    """Tests for billing history endpoints."""
    
    def test_get_billing_history(
        self, client, school_admin_headers, sample_billing_history
    ):
        """Test GET /billing-history/ returns billing history."""
        response = client.get('/billing-history/', headers=school_admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_billing_history_without_auth(self, client):
        """Test GET /billing-history/ without auth returns 401."""
        response = client.get('/billing-history/')
        
        assert response.status_code == 401
    
    def test_get_billing_history_with_staff_auth(self, client, staff_headers):
        """Test GET /billing-history/ with staff auth returns 403."""
        response = client.get('/billing-history/', headers=staff_headers)
        
        assert response.status_code == 403
    
    def test_post_billing_history(self, client, school_admin_headers):
        """Test POST /billing-history/ creates billing record."""
        payload = {
            "data": {
                "amount_due": 200.0,
                "payment_reference": "TEST-REF-456",
                "subscription_package": "premium"
            }
        }
        
        response = client.post(
            '/billing-history/',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['amount_due'] == 200.0
    
    def test_get_single_billing_history(
        self, client, school_admin_headers, sample_billing_history
    ):
        """Test GET /billing-history/<id>/ returns single billing record."""
        response = client.get(
            f'/billing-history/{sample_billing_history.id}/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['id'] == sample_billing_history.id
    
    def test_get_single_billing_history_nonexistent(
        self, client, school_admin_headers
    ):
        """Test GET /billing-history/<id>/ with nonexistent ID."""
        response = client.get(
            '/billing-history/99999/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 404 or response.status_code == 500


class TestSubscription:
    """Tests for POST /subscribe endpoint."""
    
    def test_post_subscribe_creates_billing_and_payment(
        self, client, school_admin_headers, mock_paystack
    ):
        """Test POST /subscribe creates billing and initiates payment."""
        payload = {
            "data": {
                "subscription_package": "premium",
                "students_number": 50
            }
        }
        
        response = client.post(
            '/subscribe',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'authorization_url' in data['data']
        assert 'reference' in data['data']
        assert mock_paystack.create_payment.called
    
    def test_post_subscribe_without_auth(self, client):
        """Test POST /subscribe without auth returns 401."""
        payload = {
            "data": {
                "subscription_package": "premium",
                "students_number": 50
            }
        }
        
        response = client.post(
            '/subscribe',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_post_subscribe_missing_package(self, client, school_admin_headers):
        """Test POST /subscribe without subscription_package returns validation error."""
        payload = {
            "data": {
                "students_number": 50
            }
        }
        
        response = client.post(
            '/subscribe',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 422
    
    def test_post_subscribe_missing_students_number(
        self, client, school_admin_headers
    ):
        """Test POST /subscribe without students_number returns validation error."""
        payload = {
            "data": {
                "subscription_package": "premium"
            }
        }
        
        response = client.post(
            '/subscribe',
            data=json.dumps(payload),
            content_type='application/json',
            headers=school_admin_headers
        )
        
        assert response.status_code == 422


class TestSettleBilling:
    """Tests for GET /billing-history/<id>/settle/ endpoint."""
    
    def test_get_settle_billing_creates_payment(
        self, client, school_admin_headers, sample_billing_history, mock_paystack
    ):
        """Test GET /billing-history/<id>/settle/ initiates payment."""
        # First, mark it as pending
        sample_billing_history.payment_status = 'pending'
        sample_billing_history.save()
        
        response = client.get(
            f'/billing-history/{sample_billing_history.id}/settle/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'authorization_url' in data['data']
    
    def test_get_settle_billing_already_paid(
        self, client, school_admin_headers, sample_billing_history
    ):
        """Test GET /billing-history/<id>/settle/ for already paid billing."""
        # Billing is already marked as success in fixture
        response = client.get(
            f'/billing-history/{sample_billing_history.id}/settle/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200 or response.status_code == 201
    
    def test_get_settle_billing_nonexistent(self, client, school_admin_headers):
        """Test GET /billing-history/<id>/settle/ with nonexistent ID."""
        response = client.get(
            '/billing-history/99999/settle/',
            headers=school_admin_headers
        )
        
        assert response.status_code == 404 or response.status_code == 500


class TestPaymentConfirmation:
    """Tests for GET /payment/<reference>/confirm/ endpoint."""
    
    def test_get_payment_confirm_success(
        self, client, sample_billing_history, sample_school, mock_paystack
    ):
        """Test GET /payment/<reference>/confirm/ verifies payment."""
        # Set billing as pending
        sample_billing_history.payment_status = 'pending'
        sample_billing_history.save()
        
        response = client.get(
            f'/payment/{sample_billing_history.payment_reference}/confirm/'
        )
        
        assert response.status_code == 200
        assert mock_paystack.verify_payment.called
    
    def test_get_payment_confirm_already_successful(
        self, client, sample_billing_history
    ):
        """Test GET /payment/<reference>/confirm/ for already confirmed payment."""
        # Billing is already success in fixture
        response = client.get(
            f'/payment/{sample_billing_history.payment_reference}/confirm/'
        )
        
        assert response.status_code == 200
    
    def test_get_payment_confirm_nonexistent_reference(self, client, mock_paystack):
        """Test GET /payment/<reference>/confirm/ with nonexistent reference."""
        response = client.get('/payment/NONEXISTENT-REF/confirm/')
        
        assert response.status_code == 404
    
    def test_get_payment_confirm_no_auth_required(
        self, client, sample_billing_history, mock_paystack
    ):
        """Test GET /payment/<reference>/confirm/ doesn't require authentication."""
        response = client.get(
            f'/payment/{sample_billing_history.payment_reference}/confirm/'
        )
        
        # Should work without authentication
        assert response.status_code in [200, 400]


class TestPaystackWebhook:
    """Tests for POST /paystack-webhook/ endpoint."""
    
    def test_post_paystack_webhook_charge_success(
        self, client, sample_billing_history, sample_school
    ):
        """Test POST /paystack-webhook/ processes successful charge."""
        # Set billing as pending
        sample_billing_history.payment_status = 'pending'
        sample_billing_history.save()
        
        payload = {
            'event': 'charge.success',
            'data': {
                'reference': sample_billing_history.payment_reference,
                'status': 'success'
            }
        }
        
        response = client.post(
            '/paystack-webhook/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_post_paystack_webhook_charge_failed(
        self, client, sample_billing_history
    ):
        """Test POST /paystack-webhook/ processes failed charge."""
        sample_billing_history.payment_status = 'pending'
        sample_billing_history.save()
        
        payload = {
            'event': 'charge.failed',
            'data': {
                'reference': sample_billing_history.payment_reference
            }
        }
        
        response = client.post(
            '/paystack-webhook/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_post_paystack_webhook_nonexistent_reference(self, client):
        """Test POST /paystack-webhook/ with nonexistent payment reference."""
        payload = {
            'event': 'charge.success',
            'data': {
                'reference': 'NONEXISTENT-REF'
            }
        }
        
        response = client.post(
            '/paystack-webhook/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 404
    
    def test_post_paystack_webhook_already_successful(
        self, client, sample_billing_history
    ):
        """Test POST /paystack-webhook/ for already successful payment."""
        # Billing already marked as success
        payload = {
            'event': 'charge.success',
            'data': {
                'reference': sample_billing_history.payment_reference
            }
        }
        
        response = client.post(
            '/paystack-webhook/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_post_paystack_webhook_no_auth_required(self, client):
        """Test POST /paystack-webhook/ doesn't require authentication."""
        payload = {
            'event': 'charge.success',
            'data': {
                'reference': 'TEST-REF'
            }
        }
        
        response = client.post(
            '/paystack-webhook/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should work without authentication (404 because ref doesn't exist)
        assert response.status_code in [200, 404]


class TestBillingProcess:
    """Tests for GET /billing-process/ endpoint."""
    
    def test_get_billing_process_with_valid_code(self, client, app):
        """Test GET /billing-process/ with valid code parameter."""
        with app.app_context():
            from globals import APP_SECRET_KEY
            response = client.get(f'/billing-process/?code={APP_SECRET_KEY}')
            
            assert response.status_code == 200
    
    def test_get_billing_process_without_code(self, client):
        """Test GET /billing-process/ without code returns 403."""
        response = client.get('/billing-process/')
        
        assert response.status_code == 403
    
    def test_get_billing_process_with_invalid_code(self, client):
        """Test GET /billing-process/ with invalid code returns 403."""
        response = client.get('/billing-process/?code=invalid-code')
        
        assert response.status_code == 403
    
    def test_get_billing_process_no_auth_required(self, client, app):
        """Test GET /billing-process/ doesn't require user authentication."""
        with app.app_context():
            from globals import APP_SECRET_KEY
            # Should work without user authentication, just needs the secret code
            response = client.get(f'/billing-process/?code={APP_SECRET_KEY}')
            
            assert response.status_code == 200
