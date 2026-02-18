"""
Tests for the Mergington High School API.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to their original state before each test."""
    original_state = {name: {**data, "participants": list(data["participants"])}
                      for name, data in activities.items()}
    yield
    activities.clear()
    activities.update(original_state)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict(self, client):
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_contains_expected_activities(self, client):
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activity_has_required_fields(self, client):
        response = client.get("/activities")
        chess = response.json()["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_participant_added_to_activity(self, client):
        email = "teststudent@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_duplicate_signup_returns_400(self, client):
        email = "michael@mergington.edu"  # already signed up for Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        email = "michael@mergington.edu"  # already in Chess Club
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_participant_removed_from_activity(self, client):
        email = "michael@mergington.edu"
        client.delete("/activities/Chess Club/signup", params={"email": email})
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_enrolled_returns_400(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not registered for this activity"
