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


class TestUpgradeEndpoint:
    """Tests for POST /subscriptions/upgrade endpoint."""

    def test_trial_school_upgrades_to_premium_termly(
        self, client, school_admin_headers, sample_school, mock_paystack
    ):
        """Trial school upgrade: expiry = trial_expiry + 105 days, tier = premium."""
        trial_expiry = datetime.now(timezone.utc).date() + timedelta(days=15)
        sample_school.subscription_tier = "trial"
        sample_school.subscription_expiry_date = trial_expiry
        sample_school.billing_cycle = None
        sample_school.save()

        response = client.post(
            "/subscriptions/upgrade",
            data=json.dumps({"data": {"tier": "premium", "billing_cycle": "termly", "seats": 50}}),
            content_type="application/json",
            headers=school_admin_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "authorization_url" in data["data"]
        assert mock_paystack.create_payment.called

    def test_free_school_upgrades_to_premium_monthly(
        self, client, school_admin_headers, sample_school, mock_paystack
    ):
        """Free school upgrade: returns Paystack URL."""
        sample_school.subscription_tier = "free"
        sample_school.billing_cycle = None
        sample_school.save()

        response = client.post(
            "/subscriptions/upgrade",
            data=json.dumps({"data": {"tier": "premium", "billing_cycle": "monthly", "seats": 30}}),
            content_type="application/json",
            headers=school_admin_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "reference" in data["data"]

    def test_invalid_tier_rejected(self, client, school_admin_headers):
        """Invalid tier returns 400."""
        response = client.post(
            "/subscriptions/upgrade",
            data=json.dumps({"data": {"tier": "super_tier", "billing_cycle": "monthly", "seats": 10}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert response.status_code == 400

    def test_invalid_billing_cycle_rejected(self, client, school_admin_headers):
        """Invalid billing_cycle returns 400."""
        response = client.post(
            "/subscriptions/upgrade",
            data=json.dumps({"data": {"tier": "premium", "billing_cycle": "biweekly", "seats": 10}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert response.status_code == 400

    def test_upgrade_requires_auth(self, client):
        """Upgrade endpoint returns 401 without auth."""
        response = client.post(
            "/subscriptions/upgrade",
            data=json.dumps({"data": {"tier": "premium", "billing_cycle": "monthly", "seats": 10}}),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_zero_seats_rejected(self, client, school_admin_headers):
        """seats=0 returns 400."""
        response = client.post(
            "/subscriptions/upgrade",
            data=json.dumps({"data": {"tier": "premium", "billing_cycle": "monthly", "seats": 0}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert response.status_code == 400


class TestUpgradePaymentConfirmation:
    """Test that confirm_payment correctly applies upgrade logic."""

    def test_confirm_upgrade_payment_applies_tier_and_expiry(
        self, client, school_admin_headers, sample_school, mock_paystack, db_session
    ):
        """Confirming an upgrade: record applies tier, cycle, expiry."""
        from app.subscriptions.models import SchoolBillingHistory

        trial_expiry = datetime.now(timezone.utc).date() + timedelta(days=15)
        sample_school.subscription_tier = "trial"
        sample_school.subscription_expiry_date = trial_expiry
        sample_school.billing_cycle = None
        sample_school.save()

        bill = SchoolBillingHistory(
            school_id=sample_school.id,
            amount_due=10500.0,
            date_due=datetime.now(timezone.utc).date(),
            billed_on=datetime.now(timezone.utc).date(),
            settled_on=None,
            payment_reference="UPGRADE-REF-001",
            payment_status="pending",
            subscription_package="upgrade:premium:termly:50",
            subscription_start_date=datetime.now(timezone.utc).date(),
            subscription_end_date=datetime.now(timezone.utc).date(),
        )
        db_session.add(bill)
        db_session.commit()

        response = client.get(
            "/payment/UPGRADE-REF-001/confirm/",
            headers=school_admin_headers,
        )

        assert response.status_code == 200
        db_session.refresh(sample_school)
        assert sample_school.subscription_tier == "premium"
        assert sample_school.billing_cycle == "termly"
        assert sample_school.total_seats == 50
        assert sample_school.subscription_expiry_date == trial_expiry + timedelta(days=105)


class TestApplyRenewal:
    """Tests for apply_renewal_if_due logic."""

    def test_trial_school_expired_converts_to_free(self, app, db_session):
        """Trial school with expired subscription converts to free."""
        from app.school.models import School
        from app.subscriptions.subscription_manager import apply_renewal_if_due

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Trial School",
            short_name="TS",
            code="TRIAL01",
            location="City",
            subscription_tier="trial",
            subscription_package="Premium",
            subscription_expiry_date=today,
            total_seats=100,
        )
        db_session.add(school)
        db_session.commit()

        processed = apply_renewal_if_due(today=today)
        assert processed >= 1

        db_session.refresh(school)
        assert school.subscription_tier == "free"
        assert school.total_seats == 10
        assert school.billing_cycle is None

    def test_paid_school_with_scheduled_downgrade_converts_to_free(self, app, db_session):
        """Paid school with scheduled_downgrade=True converts to free on renewal."""
        from app.school.models import School
        from app.subscriptions.subscription_manager import apply_renewal_if_due

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Downgrade School",
            short_name="DS",
            code="DOWN01",
            location="City",
            subscription_tier="premium",
            subscription_package="Premium",
            billing_cycle="monthly",
            total_seats=50,
            price_per_seat=75.0,
            subscription_expiry_date=today,
            scheduled_downgrade=True,
            scheduled_downgrade_date=today,
        )
        db_session.add(school)
        db_session.commit()

        processed = apply_renewal_if_due(today=today)
        assert processed >= 1

        db_session.refresh(school)
        assert school.subscription_tier == "free"
        assert school.scheduled_downgrade is False

    def test_paid_school_with_scheduled_cycle_change_updates_cycle(self, app, db_session):
        """Paid school with scheduled cycle change updates billing_cycle, does NOT apply seat reduction."""
        from app.school.models import School
        from app.subscriptions.subscription_manager import apply_renewal_if_due

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Cycle School",
            short_name="CS",
            code="CYC01",
            location="City",
            subscription_tier="premium",
            subscription_package="Premium",
            billing_cycle="monthly",
            total_seats=50,
            price_per_seat=75.0,
            subscription_expiry_date=today,
            scheduled_billing_cycle="termly",
            scheduled_billing_cycle_date=today,
            scheduled_seat_reduction=5,
            scheduled_reduction_date=today,
        )
        db_session.add(school)
        db_session.commit()

        apply_renewal_if_due(today=today)

        db_session.refresh(school)
        assert school.billing_cycle == "termly"
        assert school.scheduled_billing_cycle is None
        assert school.scheduled_seat_reduction == 5

    def test_seat_reduction_cancelled_if_would_strand_students(self, app, db_session):
        """Seat reduction that would leave total < seats_used is cancelled."""
        from app.school.models import School
        from app.student.models import Student
        from app._shared.services import hash_password
        from app.subscriptions.subscription_manager import apply_renewal_if_due

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Reduction School",
            short_name="RS",
            code="RED01",
            location="City",
            subscription_tier="premium",
            subscription_package="Premium",
            billing_cycle="monthly",
            total_seats=15,
            price_per_seat=75.0,
            subscription_expiry_date=today,
            scheduled_seat_reduction=10,
            scheduled_reduction_date=today,
        )
        db_session.add(school)
        db_session.commit()

        for i in range(10):
            s = Student(
                first_name=f"S{i}",
                surname="Test",
                email=f"s{i}@red.test",
                password_hash=hash_password("pass"),
                is_approved=True,
                school_id=school.id,
            )
            db_session.add(s)
        db_session.commit()

        apply_renewal_if_due(today=today)

        db_session.refresh(school)
        assert school.total_seats == 15
        assert school.scheduled_seat_reduction is None

    def test_school_with_no_scheduled_changes_not_counted(self, app, db_session):
        """School with no scheduled changes but expired subscription: processed=0 for renewal step."""
        from app.school.models import School
        from app.subscriptions.subscription_manager import apply_renewal_if_due

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Plain School",
            short_name="PS",
            code="PLAIN01",
            location="City",
            subscription_tier="premium",
            subscription_package="Premium",
            billing_cycle="monthly",
            total_seats=50,
            price_per_seat=75.0,
            subscription_expiry_date=today,
        )
        db_session.add(school)
        db_session.commit()

        processed = apply_renewal_if_due(today=today)
        assert processed == 0


class TestRenewalProcess:
    """Tests for POST /renewal-process/ endpoint."""

    def test_post_renewal_process_with_valid_key(self, client):
        """POST /renewal-process/ with valid key returns 200."""
        internal_key = os.environ.get("APP_SECRET_KEY", "test-app-secret-key")
        response = client.post(
            "/renewal-process/",
            content_type="application/json",
            headers={"X-Internal-Key": internal_key},
        )
        assert response.status_code == 200

    def test_post_renewal_process_without_key_returns_403(self, client):
        """POST /renewal-process/ without key returns 403."""
        response = client.post("/renewal-process/", content_type="application/json")
        assert response.status_code == 403

    def test_post_renewal_process_with_invalid_key_returns_403(self, client):
        """POST /renewal-process/ with invalid key returns 403."""
        response = client.post(
            "/renewal-process/",
            content_type="application/json",
            headers={"X-Internal-Key": "wrong-key"},
        )
        assert response.status_code == 403


class TestSuspensionProcess:
    """Tests for POST /suspension-process/ endpoint."""

    def test_valid_key_returns_200(self, client):
        internal_key = os.environ.get("APP_SECRET_KEY", "test-app-secret-key")
        response = client.post(
            "/suspension-process/",
            content_type="application/json",
            headers={"X-Internal-Key": internal_key},
        )
        assert response.status_code == 200

    def test_no_key_returns_403(self, client):
        response = client.post("/suspension-process/", content_type="application/json")
        assert response.status_code == 403

    def test_invalid_key_returns_403(self, client):
        response = client.post(
            "/suspension-process/",
            content_type="application/json",
            headers={"X-Internal-Key": "wrong-key"},
        )
        assert response.status_code == 403

    def test_overdue_unpaid_school_demoted_to_free(self, client, db_session):
        """School with an unpaid past-due bill is demoted to free tier."""
        from app.school.models import School
        from app.subscriptions.models import SchoolBillingHistory
        from app.subscriptions.constants import PaymentStatus

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Overdue School",
            short_name="OS",
            code="OVRD01",
            location="City",
            subscription_tier="premium",
            subscription_package="Premium",
            billing_cycle="monthly",
            total_seats=50,
            price_per_seat=75.0,
            subscription_expiry_date=today - timedelta(days=10),
        )
        db_session.add(school)
        db_session.commit()

        bill = SchoolBillingHistory(
            school_id=school.id,
            amount_due=3750.0,
            date_due=today - timedelta(days=3),
            billed_on=today - timedelta(days=10),
            settled_on=None,
            payment_reference=None,
            payment_status=PaymentStatus.pending,
            subscription_package="Premium",
            subscription_start_date=today - timedelta(days=40),
            subscription_end_date=today - timedelta(days=10),
        )
        db_session.add(bill)
        db_session.commit()

        internal_key = os.environ.get("APP_SECRET_KEY", "test-app-secret-key")
        client.post(
            "/suspension-process/",
            content_type="application/json",
            headers={"X-Internal-Key": internal_key},
        )

        db_session.refresh(school)
        assert school.subscription_tier == "free"
        assert school.total_seats == 10

    def test_paid_past_due_school_not_demoted(self, client, db_session):
        """School with a paid past-due bill is NOT demoted."""
        from app.school.models import School
        from app.subscriptions.models import SchoolBillingHistory
        from app.subscriptions.constants import PaymentStatus

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Paid School",
            short_name="PS",
            code="PAID02",
            location="City",
            subscription_tier="premium",
            subscription_package="Premium",
            billing_cycle="monthly",
            total_seats=50,
            price_per_seat=75.0,
            subscription_expiry_date=today - timedelta(days=10),
        )
        db_session.add(school)
        db_session.commit()

        bill = SchoolBillingHistory(
            school_id=school.id,
            amount_due=3750.0,
            date_due=today - timedelta(days=3),
            billed_on=today - timedelta(days=10),
            settled_on=today - timedelta(days=3),
            payment_reference="PAID-REF-001",
            payment_status=PaymentStatus.success,
            subscription_package="Premium",
            subscription_start_date=today - timedelta(days=40),
            subscription_end_date=today - timedelta(days=10),
        )
        db_session.add(bill)
        db_session.commit()

        internal_key = os.environ.get("APP_SECRET_KEY", "test-app-secret-key")
        client.post(
            "/suspension-process/",
            content_type="application/json",
            headers={"X-Internal-Key": internal_key},
        )

        db_session.refresh(school)
        assert school.subscription_tier == "premium"


class TestBillingProcessCallsRenewalFirst:
    """Verify that /billing-process/ runs renewal before billing in one call."""

    def test_expired_trial_converts_to_free_and_creates_bill(self, client, db_session):
        """Single /billing-process/ call on an expired trial school:
        renewal fires (tier→free) and a billing record is created."""
        from app.school.models import School
        from app.subscriptions.models import SchoolBillingHistory

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Trial Billing School",
            short_name="TBS",
            code="TBS001",
            location="City",
            subscription_tier="trial",
            subscription_package="Premium",
            subscription_expiry_date=today,
            total_seats=100,
        )
        db_session.add(school)
        db_session.commit()

        internal_key = os.environ.get("APP_SECRET_KEY", "test-app-secret-key")
        response = client.post(
            "/billing-process/",
            content_type="application/json",
            headers={"X-Internal-Key": internal_key},
        )
        assert response.status_code == 200

        db_session.refresh(school)
        assert school.subscription_tier == "free"

        bills = SchoolBillingHistory.query.filter_by(school_id=school.id).all()
        assert len(bills) == 1


class TestUpgradeHandlerExpiryFix:
    """Tests for the corrected expiry-base logic in handle_successful_upgrade."""

    def test_active_premium_upgrade_yearly_extends_existing_expiry(self, app, db_session):
        """Active premium school (40 days left) upgrading yearly gets old_expiry + 365."""
        from app.school.models import School
        from app.subscriptions.upgrade_handler import handle_successful_upgrade

        today = datetime.now(timezone.utc).date()
        old_expiry = today + timedelta(days=40)
        school = School(
            name="Active Premium",
            short_name="AP",
            code="ACT001",
            location="City",
            subscription_tier="premium",
            subscription_package="Premium",
            billing_cycle="monthly",
            total_seats=50,
            price_per_seat=75.0,
            subscription_expiry_date=old_expiry,
        )
        db_session.add(school)
        db_session.commit()

        handle_successful_upgrade(school, "premium", "yearly", 50)

        db_session.refresh(school)
        assert school.subscription_expiry_date == old_expiry + timedelta(days=365)

    def test_stale_trial_expiry_uses_today_as_base(self, app, db_session):
        """Trial school whose expiry already passed gets today + cycle_days."""
        from app.school.models import School
        from app.subscriptions.upgrade_handler import handle_successful_upgrade

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Stale Trial",
            short_name="ST",
            code="STL001",
            location="City",
            subscription_tier="trial",
            subscription_package="Premium",
            subscription_expiry_date=today - timedelta(days=1),
            total_seats=100,
        )
        db_session.add(school)
        db_session.commit()

        handle_successful_upgrade(school, "premium", "monthly", 30)

        db_session.refresh(school)
        assert school.subscription_expiry_date == today + timedelta(days=30)

    def test_free_school_upgrade_uses_today_as_base(self, app, db_session):
        """Free school upgrade gets today + cycle_days."""
        from app.school.models import School
        from app.subscriptions.upgrade_handler import handle_successful_upgrade

        today = datetime.now(timezone.utc).date()
        school = School(
            name="Free School",
            short_name="FS",
            code="FREE02",
            location="City",
            subscription_tier="free",
            subscription_package="Free",
            total_seats=10,
            subscription_expiry_date=today + timedelta(days=5),
        )
        db_session.add(school)
        db_session.commit()

        handle_successful_upgrade(school, "premium", "monthly", 30)

        db_session.refresh(school)
        assert school.subscription_expiry_date == today + timedelta(days=30)


class TestOverdueBillingHistoryQuery:
    """Tests for the corrected get_overdue_billing_histories query."""

    def test_unpaid_past_due_bill_is_returned(self, app, db_session, sample_school):
        """Unpaid bill with date_due in the past is returned."""
        from app.subscriptions.models import SchoolBillingHistory
        from app.subscriptions.operations import sb_history_manager
        from app.subscriptions.constants import PaymentStatus

        today = datetime.now(timezone.utc).date()
        bill = SchoolBillingHistory(
            school_id=sample_school.id,
            amount_due=3750.0,
            date_due=today - timedelta(days=1),
            billed_on=today - timedelta(days=8),
            settled_on=None,
            payment_reference=None,
            payment_status=PaymentStatus.pending,
            subscription_package="Premium",
            subscription_start_date=today - timedelta(days=38),
            subscription_end_date=today - timedelta(days=8),
        )
        db_session.add(bill)
        db_session.commit()

        results = sb_history_manager.get_overdue_billing_histories(today)
        assert any(b.id == bill.id for b in results)

    def test_paid_past_due_bill_not_returned(self, app, db_session, sample_school):
        """Paid bill with date_due in the past is NOT returned."""
        from app.subscriptions.models import SchoolBillingHistory
        from app.subscriptions.operations import sb_history_manager
        from app.subscriptions.constants import PaymentStatus

        today = datetime.now(timezone.utc).date()
        bill = SchoolBillingHistory(
            school_id=sample_school.id,
            amount_due=3750.0,
            date_due=today - timedelta(days=1),
            billed_on=today - timedelta(days=8),
            settled_on=today - timedelta(days=1),
            payment_reference="PAID-REF-002",
            payment_status=PaymentStatus.success,
            subscription_package="Premium",
            subscription_start_date=today - timedelta(days=38),
            subscription_end_date=today - timedelta(days=8),
        )
        db_session.add(bill)
        db_session.commit()

        results = sb_history_manager.get_overdue_billing_histories(today)
        assert not any(b.id == bill.id for b in results)

    def test_unpaid_future_bill_not_returned(self, app, db_session, sample_school):
        """Unpaid bill with date_due in the future is NOT returned."""
        from app.subscriptions.models import SchoolBillingHistory
        from app.subscriptions.operations import sb_history_manager
        from app.subscriptions.constants import PaymentStatus

        today = datetime.now(timezone.utc).date()
        bill = SchoolBillingHistory(
            school_id=sample_school.id,
            amount_due=3750.0,
            date_due=today + timedelta(days=3),
            billed_on=today,
            settled_on=None,
            payment_reference=None,
            payment_status=PaymentStatus.pending,
            subscription_package="Premium",
            subscription_start_date=today - timedelta(days=30),
            subscription_end_date=today,
        )
        db_session.add(bill)
        db_session.commit()

        results = sb_history_manager.get_overdue_billing_histories(today)
        assert not any(b.id == bill.id for b in results)
