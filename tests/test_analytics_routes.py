"""
Comprehensive tests for analytics routes (app/analytics/routes.py)
Tests cover school analytics, student analytics, and legacy analytics endpoints.
"""

import pytest
import json
from unittest.mock import patch


class TestSchoolStaffAnalytics:
    """Tests for school/staff analytics endpoints."""
    
    def test_get_practice_rate(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /analytics/practice-rate returns practice rate data."""
        response = client.get(
            f'/analytics/practice-rate?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_get_performance_distribution(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /analytics/performance-distribution returns distribution data."""
        response = client.get(
            f'/analytics/performance-distribution?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_subject_performance(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /analytics/subject-performance returns performance data."""
        response = client.get(
            f'/analytics/subject-performance?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_recent_tests_activities(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /analytics/recent-tests-activities returns activity data."""
        response = client.get(
            f'/analytics/recent-tests-activities?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_proficiency_distribution(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /analytics/proficiency-distribution returns proficiency data."""
        response = client.get(
            f'/analytics/proficiency-distribution?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_average_score_trend(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /analytics/average-score-trend returns score trend data."""
        response = client.get(
            f'/analytics/average-score-trend?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_performance_general(
        self, client, school_admin_headers, sample_batch
    ):
        """Test GET /analytics/performance-general returns general performance data."""
        response = client.get(
            f'/analytics/performance-general?batch_id={sample_batch.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_students_proficiency(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /analytics/students-proficiency returns student proficiency data."""
        response = client.get(
            f'/analytics/students-proficiency?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_topic_level_breakdown(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test GET /analytics/topic-level-breakdown returns topic breakdown data."""
        response = client.get(
            f'/analytics/topic-level-breakdown?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_analytics_without_auth(self, client):
        """Test analytics endpoints without auth return 401."""
        response = client.get('/analytics/practice-rate')
        assert response.status_code == 401


class TestStudentSpecificAnalytics:
    """Tests for student-specific analytics endpoints."""
    
    def test_get_performance_indicators(
        self, client, student_headers, sample_student, sample_subject
    ):
        """Test GET /analytics/<id>/performance-indicators returns indicators."""
        response = client.get(
            f'/analytics/{sample_student.id}/performance-indicators?subject_id={sample_subject.id}',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_get_subject_proficiency(
        self, client, student_headers, sample_student, sample_subject
    ):
        """Test GET /analytics/<id>/subject-proficiency returns proficiency data."""
        response = client.get(
            f'/analytics/{sample_student.id}/subject-proficiency?subject_id={sample_subject.id}',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_get_test_history(
        self, client, student_headers, sample_student, sample_subject
    ):
        """Test GET /analytics/<id>/test-history returns test history."""
        response = client.get(
            f'/analytics/{sample_student.id}/test-history?subject_id={sample_subject.id}',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_get_proficiency_graph(
        self, client, student_headers, sample_student, sample_subject
    ):
        """Test GET /analytics/<id>/proficiency-graph returns graph data."""
        response = client.get(
            f'/analytics/{sample_student.id}/proficiency-graph?subject_id={sample_subject.id}',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_get_failing_topics(
        self, client, student_headers, sample_student, sample_subject
    ):
        """Test GET /analytics/<id>/failing-topics returns failing topics."""
        response = client.get(
            f'/analytics/{sample_student.id}/failing-topics?subject_id={sample_subject.id}',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_get_student_proficiency(
        self, client, student_headers, sample_student, sample_subject
    ):
        """Test GET /analytics/<id>/student-proficiency returns student proficiency."""
        response = client.get(
            f'/analytics/{sample_student.id}/student-proficiency?subject_id={sample_subject.id}',
            headers=student_headers
        )
        
        assert response.status_code == 200


class TestNewStudentAnalytics:
    """Tests for new student dashboard analytics endpoints."""
    
    def test_get_student_dashboard_overview(
        self, client, student_headers, sample_student
    ):
        """Test GET /analytics/<id>/dashboard-overview returns overview data."""
        response = client.get(
            f'/analytics/{sample_student.id}/dashboard-overview',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_get_student_practice_overview(
        self, client, student_headers, sample_student
    ):
        """Test GET /analytics/<id>/practice-insights returns practice data."""
        response = client.get(
            f'/analytics/{sample_student.id}/practice-insights',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_get_student_achievements(
        self, client, student_headers, sample_student
    ):
        """Test GET /analytics/<id>/achievements returns achievements."""
        response = client.get(
            f'/analytics/{sample_student.id}/achievements',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_get_student_weekly_goals(
        self, client, student_headers, sample_student
    ):
        """Test GET /analytics/<id>/weekly-goals returns weekly goals."""
        response = client.get(
            f'/analytics/{sample_student.id}/weekly-goals',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_get_student_weekly_wins_messages(
        self, client, student_headers, sample_student
    ):
        """Test GET /analytics/<id>/weekly-wins-messages returns wins messages."""
        response = client.get(
            f'/analytics/{sample_student.id}/weekly-wins-messages',
            headers=student_headers
        )
        
        assert response.status_code == 200
    
    def test_student_analytics_requires_student_auth(
        self, client, staff_headers, sample_student
    ):
        """Test new student analytics require student authentication."""
        response = client.get(
            f'/analytics/{sample_student.id}/dashboard-overview',
            headers=staff_headers
        )
        
        # Staff should not have access to student-only endpoints
        assert response.status_code == 403


class TestLegacyAnalytics:
    """Tests for legacy analytics endpoints."""
    
    def test_get_weekly_report(self, client, student_headers):
        """Test GET /students/dashboard/weekly-report/ returns weekly report."""
        response = client.get(
            '/students/dashboard/weekly-report/',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert 'hours_spent' in data['data']
        assert 'percentage' in data['data']
    
    def test_get_topic_performance(
        self, client, student_headers, sample_student, sample_subject
    ):
        """Test GET /students/topic-performance/ returns topic performance."""
        response = client.get(
            f'/students/topic-performance/?student_id={sample_student.id}&subject_id={sample_subject.id}',
            headers=student_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert 'best_performing_topics' in data['data']
        assert 'worst_performing_topics' in data['data']
    
    def test_get_student_performance(
        self, client, school_admin_headers, sample_subject, sample_batch
    ):
        """Test GET /student-performance/ returns performance distribution."""
        response = client.get(
            f'/student-performance/?subject_id={sample_subject.id}&batch_id={sample_batch.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_performance_summary(
        self, client, school_admin_headers, sample_subject, sample_batch
    ):
        """Test GET /performance-summary/ returns summary data."""
        response = client.get(
            f'/performance-summary/?subject_id={sample_subject.id}&batch_id={sample_batch.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_get_topic_mastery(
        self, client, school_admin_headers, sample_subject, sample_batch
    ):
        """Test GET /topic-mastery/ returns mastery data."""
        response = client.get(
            f'/topic-mastery/?subject_id={sample_subject.id}&batch_id={sample_batch.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_legacy_analytics_multi_user_access(
        self, client, staff_headers, sample_subject
    ):
        """Test legacy analytics accessible by multiple user types."""
        response = client.get(
            f'/students/topic-performance/?subject_id={sample_subject.id}',
            headers=staff_headers
        )
        
        assert response.status_code == 200


class TestAnalyticsQueryParameters:
    """Tests for analytics endpoints with various query parameters."""
    
    def test_analytics_with_missing_required_params_staff(
        self, client, staff_headers
    ):
        """Test staff analytics without required params returns error."""
        # Staff requires batch_id and subject_id
        response = client.get(
            '/analytics/practice-rate',
            headers=staff_headers
        )
        
        assert response.status_code == 400
    
    def test_analytics_school_admin_without_required_params(
        self, client, school_admin_headers
    ):
        """Test school admin can access analytics without batch/subject filters."""
        response = client.get(
            '/analytics/practice-rate',
            headers=school_admin_headers
        )
        
        # School admin can access without filters
        assert response.status_code == 200
    
    def test_analytics_with_invalid_batch_id(
        self, client, school_admin_headers, sample_subject
    ):
        """Test analytics with invalid batch_id."""
        response = client.get(
            f'/analytics/practice-rate?batch_id=99999&subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 404]
    
    def test_analytics_with_stage_filter(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test topic-level-breakdown with stage filter."""
        response = client.get(
            f'/analytics/topic-level-breakdown?batch_id={sample_batch.id}&subject_id={sample_subject.id}&stage=Stage 1-3',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_analytics_with_level_filter(
        self, client, school_admin_headers, sample_batch, sample_subject
    ):
        """Test topic-level-breakdown with level filter."""
        response = client.get(
            f'/analytics/topic-level-breakdown?batch_id={sample_batch.id}&subject_id={sample_subject.id}&level=EMERGING',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200


class TestAnalyticsAuthorizationEdgeCases:
    """Tests for authorization edge cases in analytics."""
    
    def test_student_cannot_access_school_analytics(
        self, client, student_headers, sample_batch, sample_subject
    ):
        """Test student cannot access school/staff analytics."""
        response = client.get(
            f'/analytics/practice-rate?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=student_headers
        )
        
        assert response.status_code == 403
    
    def test_staff_can_access_own_batch_analytics(
        self, client, staff_headers, sample_batch, sample_subject
    ):
        """Test staff can access analytics for their batches."""
        response = client.get(
            f'/analytics/practice-rate?batch_id={sample_batch.id}&subject_id={sample_subject.id}',
            headers=staff_headers
        )
        
        assert response.status_code == 200
    
    def test_school_admin_can_access_student_analytics(
        self, client, school_admin_headers, sample_student, sample_subject
    ):
        """Test school admin can access student-specific analytics."""
        response = client.get(
            f'/analytics/{sample_student.id}/performance-indicators?subject_id={sample_subject.id}',
            headers=school_admin_headers
        )
        
        assert response.status_code == 200
    
    def test_staff_can_access_student_analytics(
        self, client, staff_headers, sample_student, sample_subject
    ):
        """Test staff can access student-specific analytics."""
        response = client.get(
            f'/analytics/{sample_student.id}/performance-indicators?subject_id={sample_subject.id}',
            headers=staff_headers
        )
        
        assert response.status_code == 200
