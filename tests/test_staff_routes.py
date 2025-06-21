import pytest
from flask import Flask
from app import create_app
from app.staff.routes import staff
from app.staff.schemas import SchoolAdminRegister, StaffRegister
from flask.testing import FlaskClient

@pytest.fixture
def app():
    app = create_app()
    app.config.from_object("config.TestingConfig")
    return app

@pytest.fixture
def test_client(app):
    return app.test_client()

@pytest.fixture
def test_school_data():
    return {
        "school": {
            "name": "Test School",
            "code": "TEST123",
            "address": "123 Test Street",
            "phone": "+233240126470",
            "email": "test@school.com"
        },
        "school_admin": {
            "email": "admin@test.com",
            "password": "Test123!",
            "first_name": "Test",
            "last_name": "Admin",
            "phone": "+233240126470"
        }
    }

@pytest.fixture
def test_staff_data():
    return {
        "email": "teacher@test.com",
        "password": "Teacher123!",
        "first_name": "Test",
        "last_name": "Teacher",
        "phone": "+233240126470",
        "school_code": "TEST123"
    }

def test_register_school_admin(test_client, test_school_data):
    response = test_client.post(
        '/staff/school-admin/register/',
        json=test_school_data
    )
    assert response.status_code == 201
    assert response.json["message"] == "success"

def test_register_school_admin_duplicate_email(test_client, test_school_data):
    # First registration
    test_client.post('/staff/school-admin/register/', json=test_school_data)
    
    # Second registration with same email
    response = test_client.post(
        '/staff/school-admin/register/',
        json=test_school_data
    )
    assert response.status_code == 400
    assert "User with the email already exists!" in response.json["message"]

def test_register_staff(test_client, test_staff_data):
    response = test_client.post(
        '/staff/staff/register/',
        json=test_staff_data
    )
    assert response.status_code == 201
    assert response.json["message"] == "success"

def test_register_staff_duplicate_email(test_client, test_staff_data):
    # First registration
    test_client.post('/staff/staff/register/', json=test_staff_data)
    
    # Second registration with same email
    response = test_client.post(
        '/staff/staff/register/',
        json=test_staff_data
    )
    assert response.status_code == 400
    assert "User with the email already exists!" in response.json["message"]

def test_login(test_client, test_school_data):
    # Register first
    test_client.post('/staff/school-admin/register/', json=test_school_data)
    
    # Login
    login_data = {
        "email": test_school_data["school_admin"]["email"],
        "password": test_school_data["school_admin"]["password"]
    }
    response = test_client.post('/staff/login/', json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json
