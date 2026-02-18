"""
Comprehensive tests for subscription routes (app/subscriptions/routes.py)
Tests cover billing history, subscription creation, payment processing, and webhooks.
"""

import pytest
import json
import hashlib
import hmac
import os
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

        assert response.status_code in [404, 500]


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


class TestSettleBilling:
    """Tests for GET /billing-history/<id>/settle/ endpoint."""

    def test_get_settle_billing_already_paid(
        self, client, school_admin_headers, sample_billing_history
    ):
        """Test GET /billing-history/<id>/settle/ for already paid billing."""
        response = client.get(
            f'/billing-history/{sample_billing_history.id}/settle/',
            headers=school_admin_headers
        )

        assert response.status_code in [200, 201]

    def test_get_settle_billing_nonexistent(self, client, school_admin_headers):
        """Test GET /billing-history/<id>/settle/ with nonexistent ID."""
        response = client.get(
            '/billing-history/99999/settle/',
            headers=school_admin_headers
        )

        assert response.status_code in [404, 500]


class TestPaymentConfirmation:
    """Tests for GET /payment/<reference>/confirm/ endpoint."""

    def test_get_payment_confirm_already_successful(
        self, client, school_admin_headers, sample_billing_history
    ):
        """Test GET /payment/<reference>/confirm/ for already confirmed payment."""
        response = client.get(
            f'/payment/{sample_billing_history.payment_reference}/confirm/',
            headers=school_admin_headers
        )

        assert response.status_code == 200

    def test_get_payment_confirm_nonexistent_reference(self, client, school_admin_headers, mock_paystack):
        """Test GET /payment/<reference>/confirm/ with nonexistent reference."""
        response = client.get(
            '/payment/NONEXISTENT-REF/confirm/',
            headers=school_admin_headers
        )

        assert response.status_code == 404

    def test_get_payment_confirm_without_auth(self, client, sample_billing_history):
        """Test GET /payment/<reference>/confirm/ without auth returns 401."""
        response = client.get(
            f'/payment/{sample_billing_history.payment_reference}/confirm/'
        )

        assert response.status_code == 401


class TestPaystackWebhook:
    """Tests for POST /paystack-webhook/ endpoint."""

    def _make_webhook_signature(self, payload_bytes):
        """Generate a valid Paystack HMAC signature for test payloads."""
        api_key = os.environ.get("PAYSTACK_API_KEY", "test-paystack-api-key")
        return hmac.new(
            api_key.encode("utf-8"), payload_bytes, hashlib.sha512
        ).hexdigest()

    def test_post_paystack_webhook_charge_success(
        self, client, sample_billing_history, sample_school
    ):
        """Test POST /paystack-webhook/ processes successful charge."""
        sample_billing_history.payment_status = 'pending'
        sample_billing_history.save()

        payload = {
            'event': 'charge.success',
            'data': {
                'reference': sample_billing_history.payment_reference,
                'status': 'success'
            }
        }

        body = json.dumps(payload).encode("utf-8")
        sig = self._make_webhook_signature(body)

        response = client.post(
            '/paystack-webhook/',
            data=body,
            content_type='application/json',
            headers={"X-Paystack-Signature": sig}
        )

        assert response.status_code == 200

    def test_post_paystack_webhook_invalid_signature(self, client):
        """Test POST /paystack-webhook/ with invalid signature returns 403."""
        payload = {
            'event': 'charge.success',
            'data': {
                'reference': 'SOME-REF',
                'status': 'success'
            }
        }

        response = client.post(
            '/paystack-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={"X-Paystack-Signature": "invalid-sig"}
        )

        assert response.status_code == 403


class TestSeatBasedSubscriptionManager:
    def test_get_current_plan_admin_only(self, client, school_admin_headers):
        response = client.get("/subscriptions/current", headers=school_admin_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data
        assert "tier" in data["data"]
        assert "total_seats" in data["data"]

    def test_schedule_downgrade_requires_confirmation(self, client, school_admin_headers):
        response = client.post(
            "/subscriptions/schedule-downgrade",
            data=json.dumps({"data": {"confirmDowngrade": False}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert response.status_code == 400

    def test_schedule_downgrade_success(self, client, school_admin_headers, sample_school):
        sample_school.subscription_tier = "premium"
        sample_school.billing_cycle = "monthly"
        sample_school.total_seats = 15
        sample_school.price_per_seat = 75
        sample_school.save()

        response = client.post(
            "/subscriptions/schedule-downgrade",
            data=json.dumps({"data": {"confirmDowngrade": True}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["data"]["scheduled_downgrade"] is True

    def test_cancel_scheduled_downgrade(self, client, school_admin_headers, sample_school):
        sample_school.subscription_tier = "premium"
        sample_school.scheduled_downgrade = True
        sample_school.save()

        response = client.delete(
            "/subscriptions/schedule-downgrade",
            data=json.dumps({"data": {}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert response.status_code == 200

    def test_trial_account_cannot_schedule_downgrade(self, client, school_admin_headers, sample_school):
        """Trial accounts should not be able to schedule downgrades."""
        sample_school.subscription_tier = "trial"
        sample_school.subscription_expiry_date = (datetime.now(timezone.utc) + timedelta(days=30)).date()
        sample_school.save()

        response = client.post(
            "/subscriptions/schedule-downgrade",
            data=json.dumps({"data": {"confirmDowngrade": True}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "trial" in data["message"].lower()
        assert "automatically" in data["message"].lower()

    def test_paid_account_with_scheduled_downgrade_can_initiate_add_seats(self, client, school_admin_headers, sample_school, mock_paystack):
        """Paid accounts with scheduled_downgrade can still initiate add-seats (check happens at confirmation)."""
        sample_school.subscription_tier = "premium"
        sample_school.billing_cycle = "monthly"
        sample_school.total_seats = 50
        sample_school.price_per_seat = 75
        sample_school.scheduled_downgrade = True
        sample_school.subscription_expiry_date = (datetime.now(timezone.utc) + timedelta(days=30)).date()
        sample_school.save()

        response = client.post(
            "/subscriptions/add-seats",
            data=json.dumps({"data": {"seats": 10}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert response.status_code == 200


class TestBillingProcess:
    """Tests for POST /billing-process/ endpoint."""

    def test_post_billing_process_with_valid_key(self, client, app):
        """Test POST /billing-process/ with valid X-Internal-Key."""
        internal_key = os.environ.get("APP_SECRET_KEY", "test-app-secret-key")
        response = client.post(
            '/billing-process/',
            content_type='application/json',
            headers={"X-Internal-Key": internal_key}
        )

        assert response.status_code == 200

    def test_post_billing_process_without_key(self, client):
        """Test POST /billing-process/ without key returns 403."""
        response = client.post('/billing-process/', content_type='application/json')

        assert response.status_code == 403

    def test_post_billing_process_with_invalid_key(self, client):
        """Test POST /billing-process/ with invalid key returns 403."""
        response = client.post(
            '/billing-process/',
            content_type='application/json',
            headers={"X-Internal-Key": "invalid-key"}
        )

        assert response.status_code == 403
