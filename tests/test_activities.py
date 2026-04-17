"""
Tests for the Mergington High School Activities API
Uses AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    original_activities = deepcopy(activities)
    yield
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_returns_activity_details(self, client, reset_activities):
        """Test that activity details are properly returned"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        # Assert
        assert response.status_code == 200
        assert required_fields.issubset(chess_club.keys())
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_includes_current_participants(self, client, reset_activities):
        """Test that current participants are included in the response"""
        # Arrange
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club_participants = data["Chess Club"]["participants"]
        
        # Assert
        assert response.status_code == 200
        assert len(chess_club_participants) == 2
        assert all(participant in chess_club_participants for participant in expected_participants)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        email = "alice@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]
        assert "message" in response.json()

    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup properly adds participant to activity"""
        # Arrange
        email = "bob@mergington.edu"
        activity = "Programming Class"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        client.post(f"/activities/{activity}/signup", params={"email": email})
        new_count = len(activities[activity]["participants"])
        
        # Assert
        assert new_count == initial_count + 1
        assert activities[activity]["participants"][-1] == email

    def test_signup_duplicate_email_returns_error(self, client, reset_activities):
        """Test that signing up with duplicate email returns 400 error"""
        # Arrange
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signing up for non-existent activity returns 404"""
        # Arrange
        email = "charlie@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities"""
        # Arrange
        email = "david@mergington.edu"
        activities_to_join = ["Chess Club", "Soccer Team"]
        
        # Act
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        for activity in activities_to_join:
            assert email in activities[activity]["participants"]


class TestRemoveFromActivity:
    """Tests for POST /activities/{activity_name}/remove endpoint"""

    def test_remove_participant_successful(self, client, reset_activities):
        """Test successful removal of participant from activity"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        assert email in activities[activity]["participants"]
        
        # Act
        response = client.post(
            f"/activities/{activity}/remove",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in data["message"]
        assert email not in activities[activity]["participants"]

    def test_remove_reduces_participant_count(self, client, reset_activities):
        """Test that removal properly reduces participant count"""
        # Arrange
        email = "daniel@mergington.edu"
        activity = "Chess Club"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        client.post(f"/activities/{activity}/remove", params={"email": email})
        new_count = len(activities[activity]["participants"])
        
        # Assert
        assert new_count == initial_count - 1

    def test_remove_nonexistent_participant_returns_error(self, client, reset_activities):
        """Test that removing non-existent participant returns 400"""
        # Arrange
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/remove",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in data["detail"].lower()

    def test_remove_from_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that removing from non-existent activity returns 404"""
        # Arrange
        email = "someone@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity}/remove",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()

    def test_signup_then_remove_workflow(self, client, reset_activities):
        """Test complete signup and removal workflow"""
        # Arrange
        email = "emily@mergington.edu"
        activity = "Drama Club"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Act - Remove
        remove_response = client.post(
            f"/activities/{activity}/remove",
            params={"email": email}
        )
        
        # Assert
        assert remove_response.status_code == 200
        assert email not in activities[activity]["participants"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_activity_name_with_spaces_handled_correctly(self, client, reset_activities):
        """Test that activities with spaces in names are handled correctly"""
        # Arrange
        activity = "Chess Club"  # Has space in name
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]

    def test_email_case_sensitive_for_duplicates(self, client, reset_activities):
        """Test that email comparison is case-sensitive for duplicates"""
        # Arrange
        original_email = "michael@mergington.edu"
        different_case_email = "MICHAEL@mergington.edu"
        activity = "Soccer Team"
        
        # Act
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": different_case_email}
        )
        
        # Assert - different case should be allowed (treated as different email)
        assert response1.status_code == 200

    def test_empty_participants_list_for_new_signup(self, client, reset_activities):
        """Test that removing all participants results in empty list"""
        # Arrange
        activity = "Chess Club"
        participants = list(activities[activity]["participants"])  # Copy list
        
        # Act - Remove all participants
        for email in participants:
            client.post(
                f"/activities/{activity}/remove",
                params={"email": email}
            )
        
        # Assert
        assert len(activities[activity]["participants"]) == 0
