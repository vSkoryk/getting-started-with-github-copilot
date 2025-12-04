"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
    })


def test_root_redirect(client):
    """Test that root redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert len(data["Chess Club"]["participants"]) == 2
    assert data["Chess Club"]["max_participants"] == 12


def test_signup_for_activity(client):
    """Test signing up a student for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
    
    # Verify the student was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_duplicate_student(client):
    """Test that signing up the same student twice fails"""
    email = "michael@mergington.edu"  # Already in Chess Club
    response = client.post(
        f"/activities/Chess Club/signup?email={email}"
    )
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"].lower()


def test_signup_nonexistent_activity(client):
    """Test signing up for a non-existent activity"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_unregister_from_activity(client):
    """Test unregistering a student from an activity"""
    email = "michael@mergington.edu"
    response = client.delete(
        f"/activities/Chess Club/unregister?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered" in data["message"]
    assert email in data["message"]
    
    # Verify the student was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email not in activities_data["Chess Club"]["participants"]


def test_unregister_not_signed_up_student(client):
    """Test unregistering a student who is not signed up"""
    email = "notsignedup@mergington.edu"
    response = client.delete(
        f"/activities/Chess Club/unregister?email={email}"
    )
    assert response.status_code == 400
    data = response.json()
    assert "not signed up" in data["detail"].lower()


def test_unregister_nonexistent_activity(client):
    """Test unregistering from a non-existent activity"""
    response = client.delete(
        "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_multiple_signups_until_full(client):
    """Test signing up multiple students until activity is full"""
    # Create a small activity for testing
    activities["Small Club"] = {
        "description": "A small test club",
        "schedule": "Mondays",
        "max_participants": 3,
        "participants": ["student1@mergington.edu"]
    }
    
    # Sign up two more students (should succeed)
    response1 = client.post("/activities/Small Club/signup?email=student2@mergington.edu")
    assert response1.status_code == 200
    
    response2 = client.post("/activities/Small Club/signup?email=student3@mergington.edu")
    assert response2.status_code == 200
    
    # Verify all three are signed up
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert len(activities_data["Small Club"]["participants"]) == 3
