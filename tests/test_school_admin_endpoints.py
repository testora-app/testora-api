"""Tests for the admin school-management endpoints (edit, staff, students,
billing history, password reset)."""

import json

from app._shared.services import check_password
from app.staff.operations import staff_manager


class TestSchoolAdminEndpoints:
    def test_get_single_school(self, client, auth_headers, sample_school):
        resp = client.get(f"/schools/{sample_school.id}/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["id"] == sample_school.id
        assert data["name"] == sample_school.name

    def test_get_single_school_not_found(self, client, auth_headers):
        resp = client.get("/schools/999999/", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_single_school_includes_counts(
        self, client, auth_headers, sample_school, sample_staff, sample_student
    ):
        resp = client.get(f"/schools/{sample_school.id}/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["staff_count"] == 1
        assert data["student_count"] == 1
        assert data["seats_used"] == 1  # sample_student is approved + not archived

    def test_schools_list_includes_counts(
        self, client, auth_headers, sample_school, sample_staff, sample_student
    ):
        resp = client.get("/schools/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        entry = next(s for s in data if s["id"] == sample_school.id)
        assert entry["staff_count"] == 1
        assert entry["student_count"] == 1
        assert entry["seats_used"] == 1
        assert entry["total_seats"] == sample_school.total_seats

    def test_edit_school(self, client, auth_headers, sample_school):
        payload = {
            "data": {
                "name": "Renamed Academy",
                "location": "Kumasi",
                "phone_number": "+233200000000",
                "is_suspended": True,
                "subscription_tier": "premium_plus",
                "total_seats": 123,
                "subscription_expiry_date": "2027-01-15",
            }
        }
        resp = client.put(
            f"/schools/{sample_school.id}/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["name"] == "Renamed Academy"
        assert data["location"] == "Kumasi"
        assert data["is_suspended"] is True
        assert data["subscription_tier"] == "premium_plus"
        assert data["total_seats"] == 123

    def test_edit_school_bad_seats(self, client, auth_headers, sample_school):
        payload = {"data": {"total_seats": "not-a-number"}}
        resp = client.put(
            f"/schools/{sample_school.id}/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_get_school_staff(self, client, auth_headers, sample_school, sample_staff):
        resp = client.get(f"/schools/{sample_school.id}/staff/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        emails = [s["email"] for s in data]
        assert sample_staff.email in emails

    def test_get_school_students(self, client, auth_headers, sample_school, sample_student):
        resp = client.get(f"/schools/{sample_school.id}/students/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        emails = [s["email"] for s in data]
        assert sample_student.email in emails

    def test_get_school_billing_history(
        self, client, auth_headers, sample_school, sample_billing_history
    ):
        resp = client.get(
            f"/schools/{sample_school.id}/billing-history/", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert any(b["payment_reference"] == "TEST-REF-123" for b in data)

    def test_reset_password_set_mode(self, client, auth_headers, app, sample_staff):
        payload = {"data": {"user_type": "staff", "user_id": sample_staff.id, "mode": "set"}}
        resp = client.post(
            "/schools/reset-user-password/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["mode"] == "set"
        temp = data["temporary_password"]
        assert len(temp) >= 8
        with app.app_context():
            refreshed = staff_manager.get_staff_by_id(sample_staff.id)
            assert check_password(refreshed.password_hash, temp)

    def test_reset_password_email_mode(
        self, client, auth_headers, sample_student, mock_mailer
    ):
        payload = {
            "data": {"user_type": "student", "user_id": sample_student.id, "mode": "email"}
        }
        resp = client.post(
            "/schools/reset-user-password/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["mode"] == "email"
        assert mock_mailer.send_email.called

    def test_reset_password_invalid_user_type(self, client, auth_headers):
        payload = {"data": {"user_type": "alien", "user_id": 1, "mode": "set"}}
        resp = client.post(
            "/schools/reset-user-password/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_endpoints_require_admin(self, client, school_admin_headers, sample_school):
        resp = client.get(f"/schools/{sample_school.id}/staff/", headers=school_admin_headers)
        assert resp.status_code in (401, 403)

    def test_admin_edit_staff(self, client, auth_headers, sample_staff):
        payload = {
            "data": {
                "first_name": "Janet",
                "email": "janet.updated@testora.test",
                "is_admin": True,
                "is_approved": False,
            }
        }
        resp = client.put(
            f"/schools/staff/{sample_staff.id}/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["first_name"] == "Janet"
        assert data["email"] == "janet.updated@testora.test"
        assert data["is_admin"] is True
        assert data["is_approved"] is False

    def test_admin_edit_staff_duplicate_email(
        self, client, auth_headers, sample_staff, sample_school_admin
    ):
        payload = {"data": {"email": sample_school_admin.email}}
        resp = client.put(
            f"/schools/staff/{sample_staff.id}/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_admin_edit_staff_not_found(self, client, auth_headers):
        resp = client.put(
            "/schools/staff/999999/",
            data=json.dumps({"data": {"first_name": "X"}}),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_admin_edit_student(self, client, auth_headers, sample_student):
        payload = {
            "data": {
                "first_name": "Alicia",
                "is_approved": False,
                "is_archived": True,
            }
        }
        resp = client.put(
            f"/schools/students/{sample_student.id}/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["first_name"] == "Alicia"
        assert data["is_approved"] is False
        assert data["is_archived"] is True

    def test_admin_edit_student_requires_admin(
        self, client, school_admin_headers, sample_student
    ):
        resp = client.put(
            f"/schools/students/{sample_student.id}/",
            data=json.dumps({"data": {"is_archived": True}}),
            content_type="application/json",
            headers=school_admin_headers,
        )
        assert resp.status_code in (401, 403)
