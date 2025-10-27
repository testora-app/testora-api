"""
Comprehensive test fixtures for Flask API testing.
Provides database setup, authentication tokens, test data, and mocked external services.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from app import create_app
from app.extensions import db
from app._shared.services import hash_password, generate_access_token
from app._shared.schemas import UserTypes

# Import all models needed for fixtures
from app.app_admin.models import Admin, Subject, Topic, Theme
from app.school.models import School
from app.staff.models import Staff
from app.student.models import Student, Batch, StudentSubjectLevel
from app.test.models import Question, Test
from app.notifications.models import Notification, Recipient
from app.subscriptions.models import SchoolBillingHistory
from app.achievements.models import Achievement, StudentHasAchievement


# ============================================================================
# APP AND DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application instance."""
    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Provide a database session for a test."""
    with app.app_context():
        yield db.session
        db.session.rollback()


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def admin_token(app, sample_admin):
    """Generate a valid admin authentication token."""
    with app.app_context():
        token = generate_access_token(
            sample_admin.id,
            UserTypes.admin,
            sample_admin.email,
            None,
            None
        )
        return token


@pytest.fixture
def school_admin_token(app, sample_school_admin, sample_school):
    """Generate a valid school admin authentication token."""
    with app.app_context():
        token = generate_access_token(
            sample_school_admin.id,
            UserTypes.school_admin,
            sample_school_admin.email,
            sample_school.id,
            is_school_suspended=False,
            school_package='premium'
        )
        return token


@pytest.fixture
def staff_token(app, sample_staff, sample_school):
    """Generate a valid staff authentication token."""
    with app.app_context():
        token = generate_access_token(
            sample_staff.id,
            UserTypes.staff,
            sample_staff.email,
            sample_school.id,
            is_school_suspended=False,
            school_package='premium'
        )
        return token


@pytest.fixture
def student_token(app, sample_student, sample_school):
    """Generate a valid student authentication token."""
    with app.app_context():
        token = generate_access_token(
            sample_student.id,
            UserTypes.student,
            sample_student.email,
            sample_school.id,
            is_school_suspended=False,
            school_package='premium'
        )
        return token


@pytest.fixture
def expired_token(app):
    """Generate an expired authentication token."""
    with app.app_context():
        payload = {
            'user_id': 1,
            'user_type': UserTypes.student,
            'exp': datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        return token


@pytest.fixture
def invalid_token():
    """Return an invalid authentication token."""
    return 'invalid.token.here'


@pytest.fixture
def auth_headers(admin_token):
    """Return authorization headers with admin token."""
    return {'Authorization': f'Bearer {admin_token}'}


@pytest.fixture
def school_admin_headers(school_admin_token):
    """Return authorization headers with school admin token."""
    return {'Authorization': f'Bearer {school_admin_token}'}


@pytest.fixture
def staff_headers(staff_token):
    """Return authorization headers with staff token."""
    return {'Authorization': f'Bearer {staff_token}'}


@pytest.fixture
def student_headers(student_token):
    """Return authorization headers with student token."""
    return {'Authorization': f'Bearer {student_token}'}


# ============================================================================
# ADMIN DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_admin(app, db_session):
    """Create a sample admin user."""
    admin = Admin(
        username='testadmin',
        email='admin@testora.test',
        password_hash=hash_password('password123'),
        is_super_admin=True
    )
    db_session.add(admin)
    db_session.commit()
    return admin


# ============================================================================
# SCHOOL DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_school(app, db_session):
    """Create a sample school."""
    school = School(
        name='Test High School',
        code='TEST001',
        location='Test City',
        subscription_package='premium',
        subscription_expiry_date=datetime.now(timezone.utc).date() + timedelta(days=30),
        is_suspended=False
    )
    db_session.add(school)
    db_session.commit()
    return school


@pytest.fixture
def sample_free_school(app, db_session):
    """Create a sample school with free subscription."""
    school = School(
        name='Free Test School',
        code='FREE001',
        location='Test City',
        subscription_package='free',
        subscription_expiry_date=datetime.now(timezone.utc).date() + timedelta(days=30),
        is_suspended=False
    )
    db_session.add(school)
    db_session.commit()
    return school


@pytest.fixture
def suspended_school(app, db_session):
    """Create a suspended school."""
    school = School(
        name='Suspended School',
        code='SUSP001',
        location='Test City',
        subscription_package='free',
        subscription_expiry_date=datetime.now(timezone.utc).date() - timedelta(days=30),
        is_suspended=True
    )
    db_session.add(school)
    db_session.commit()
    return school


# ============================================================================
# STAFF DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_school_admin(app, db_session, sample_school):
    """Create a sample school admin."""
    admin = Staff(
        first_name='John',
        surname='Admin',
        other_names='Test',
        email='schooladmin@testora.test',
        password_hash=hash_password('password123'),
        is_admin=True,
        is_approved=True,
        school_id=sample_school.id
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def sample_staff(app, db_session, sample_school):
    """Create a sample staff member."""
    staff = Staff(
        first_name='Jane',
        surname='Teacher',
        other_names='Test',
        email='teacher@testora.test',
        password_hash=hash_password('password123'),
        is_admin=False,
        is_approved=True,
        school_id=sample_school.id
    )
    db_session.add(staff)
    db_session.commit()
    return staff


@pytest.fixture
def unapproved_staff(app, db_session, sample_school):
    """Create an unapproved staff member."""
    staff = Staff(
        first_name='Bob',
        surname='Pending',
        other_names='Test',
        email='pending@testora.test',
        password_hash=hash_password('password123'),
        is_admin=False,
        is_approved=False,
        school_id=sample_school.id
    )
    db_session.add(staff)
    db_session.commit()
    return staff


# ============================================================================
# STUDENT DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_student(app, db_session, sample_school):
    """Create a sample student."""
    student = Student(
        first_name='Alice',
        surname='Student',
        other_names='Test',
        email='student@testora.test',
        password_hash=hash_password('password123'),
        is_approved=True,
        school_id=sample_school.id,
        current_streak=5,
        longest_streak=10,
        last_test_date=datetime.now(timezone.utc).date()
    )
    db_session.add(student)
    db_session.commit()
    return student


@pytest.fixture
def unapproved_student(app, db_session, sample_school):
    """Create an unapproved student."""
    student = Student(
        first_name='Charlie',
        surname='Pending',
        other_names='Test',
        email='pendingstudent@testora.test',
        password_hash=hash_password('password123'),
        is_approved=False,
        school_id=sample_school.id
    )
    db_session.add(student)
    db_session.commit()
    return student


@pytest.fixture
def multiple_students(app, db_session, sample_school):
    """Create multiple students for batch testing."""
    students = []
    for i in range(5):
        student = Student(
            first_name=f'Student{i}',
            surname=f'Test{i}',
            email=f'student{i}@testora.test',
            password_hash=hash_password('password123'),
            is_approved=True,
            school_id=sample_school.id
        )
        db_session.add(student)
        students.append(student)
    db_session.commit()
    return students


# ============================================================================
# BATCH DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_batch(app, db_session, sample_school, sample_student):
    """Create a sample batch."""
    batch = Batch(
        batch_name='Form 3A',
        curriculum='bece',
        school_id=sample_school.id
    )
    batch.students = [sample_student]
    db_session.add(batch)
    db_session.commit()
    return batch


# ============================================================================
# CURRICULUM DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_subject(app, db_session):
    """Create a sample subject."""
    subject = Subject(
        name='Mathematics',
        short_name='Math',
        curriculum='bece',
        is_premium=False,
        max_duration=60
    )
    db_session.add(subject)
    db_session.commit()
    return subject


@pytest.fixture
def premium_subject(app, db_session):
    """Create a premium subject."""
    subject = Subject(
        name='Advanced Physics',
        short_name='Adv Physics',
        curriculum='bece',
        is_premium=True,
        max_duration=90
    )
    db_session.add(subject)
    db_session.commit()
    return subject


@pytest.fixture
def sample_theme(app, db_session, sample_subject):
    """Create a sample theme."""
    theme = Theme(
        name='Algebra',
        short_name='Alg',
        subject_id=sample_subject.id
    )
    db_session.add(theme)
    db_session.commit()
    return theme


@pytest.fixture
def sample_topic(app, db_session, sample_subject, sample_theme):
    """Create a sample topic."""
    topic = Topic(
        name='Linear Equations',
        short_name='Lin Eq',
        subject_id=sample_subject.id,
        theme_id=sample_theme.id
    )
    db_session.add(topic)
    db_session.commit()
    return topic


@pytest.fixture
def multiple_subjects(app, db_session):
    """Create multiple subjects."""
    subjects = []
    subject_names = [
        ('Mathematics', 'Math'),
        ('English', 'Eng'),
        ('Science', 'Sci'),
        ('Social Studies', 'SS')
    ]
    for name, short_name in subject_names:
        subject = Subject(
            name=name,
            short_name=short_name,
            curriculum='bece',
            is_premium=False,
            max_duration=60
        )
        db_session.add(subject)
        subjects.append(subject)
    db_session.commit()
    return subjects


# ============================================================================
# QUESTION AND TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_question(app, db_session, sample_subject, sample_topic):
    """Create a sample question."""
    question = Question(
        question_text='What is 2 + 2?',
        question_type='multiple_choice',
        options=['2', '3', '4', '5'],
        correct_answer='4',
        subject_id=sample_subject.id,
        topic_id=sample_topic.id,
        difficulty_level=1,
        year=2024,
        is_flagged=False
    )
    db_session.add(question)
    db_session.commit()
    return question


@pytest.fixture
def multiple_questions(app, db_session, sample_subject, sample_topic):
    """Create multiple questions for testing."""
    questions = []
    for i in range(10):
        question = Question(
            question_text=f'Test question {i}?',
            question_type='multiple_choice',
            options=[f'A{i}', f'B{i}', f'C{i}', f'D{i}'],
            correct_answer=f'A{i}',
            subject_id=sample_subject.id,
            topic_id=sample_topic.id,
            difficulty_level=1,
            year=2024,
            is_flagged=False
        )
        db_session.add(question)
        questions.append(question)
    db_session.commit()
    return questions


@pytest.fixture
def sample_test(app, db_session, sample_student, sample_subject, sample_question):
    """Create a sample test."""
    test = Test(
        student_id=sample_student.id,
        subject_id=sample_subject.id,
        school_id=sample_student.school_id,
        questions=[sample_question.to_json(include_correct_answer=False)],
        total_points=1,
        question_number=1,
        is_completed=False
    )
    db_session.add(test)
    db_session.commit()
    return test


@pytest.fixture
def completed_test(app, db_session, sample_student, sample_subject):
    """Create a completed test."""
    test = Test(
        student_id=sample_student.id,
        subject_id=sample_subject.id,
        school_id=sample_student.school_id,
        questions=[],
        total_points=10,
        question_number=10,
        questions_correct=8,
        points_acquired=8,
        score_acquired=80.0,
        is_completed=True,
        finished_on=datetime.now(timezone.utc)
    )
    db_session.add(test)
    db_session.commit()
    return test


# ============================================================================
# STUDENT LEVEL FIXTURES
# ============================================================================

@pytest.fixture
def student_subject_level(app, db_session, sample_student, sample_subject):
    """Create a student subject level."""
    level = StudentSubjectLevel(
        student_id=sample_student.id,
        subject_id=sample_subject.id,
        level=1,
        points=0
    )
    db_session.add(level)
    db_session.commit()
    return level


# ============================================================================
# NOTIFICATION FIXTURES
# ============================================================================

@pytest.fixture
def sample_recipient(app, db_session):
    """Create a sample notification recipient."""
    recipient = Recipient(
        user_type=UserTypes.student,
        device_ids=['test-device-id'],
        email='student@testora.test'
    )
    db_session.add(recipient)
    db_session.commit()
    return recipient


@pytest.fixture
def sample_notification(app, db_session, sample_recipient):
    """Create a sample notification."""
    notification = Notification(
        title='Test Notification',
        content='This is a test notification',
        notification_type='test',
        recipient_id=sample_recipient.id,
        is_read=False
    )
    db_session.add(notification)
    db_session.commit()
    return notification


# ============================================================================
# SUBSCRIPTION FIXTURES
# ============================================================================

@pytest.fixture
def sample_billing_history(app, db_session, sample_school):
    """Create a sample billing history entry."""
    billing = SchoolBillingHistory(
        school_id=sample_school.id,
        amount_due=100.0,
        date_due=datetime.now(timezone.utc).date(),
        billed_on=datetime.now(timezone.utc).date(),
        settled_on=datetime.now(timezone.utc).date(),
        payment_reference='TEST-REF-123',
        payment_status='success',
        subscription_package='premium',
        subscription_start_date=datetime.now(timezone.utc).date(),
        subscription_end_date=datetime.now(timezone.utc).date() + timedelta(days=31)
    )
    db_session.add(billing)
    db_session.commit()
    return billing


# ============================================================================
# ACHIEVEMENT FIXTURES
# ============================================================================

@pytest.fixture
def sample_achievement(app, db_session):
    """Create a sample achievement."""
    achievement = Achievement(
        name='First Test',
        description='Complete your first test',
        achievement_class='test',
        image_url='https://example.com/achievement.png',
        points=10
    )
    db_session.add(achievement)
    db_session.commit()
    return achievement


# ============================================================================
# MOCK EXTERNAL SERVICES
# ============================================================================

@pytest.fixture
def mock_mailer():
    """Mock the mailer service."""
    with patch('app.integrations.mailer.mailer') as mock:
        mock.send_email = MagicMock(return_value=True)
        mock.generate_email_text = MagicMock(return_value='<html>Test Email</html>')
        yield mock


@pytest.fixture
def mock_pusher():
    """Mock the Pusher notification service."""
    with patch('app.integrations.pusher.pusher') as mock:
        mock.notify_devices = MagicMock(return_value=True)
        yield mock


@pytest.fixture
def mock_paystack():
    """Mock the Paystack payment service."""
    with patch('app.integrations.paystack.paystack') as mock:
        mock.create_payment = MagicMock(return_value={
            'status': True,
            'data': {
                'authorization_url': 'https://paystack.test/pay',
                'reference': 'TEST-REF-123',
                'access_code': 'TEST-ACCESS-CODE'
            }
        })
        mock.verify_payment = MagicMock(return_value={
            'status': True,
            'data': {
                'status': 'success'
            }
        })
        yield mock


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def json_content_type():
    """Return JSON content type header."""
    return {'Content-Type': 'application/json'}
