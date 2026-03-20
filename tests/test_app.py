import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

client = TestClient(app)

# Capture the original state of the in-memory database once at import time
_original_activities = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after each test."""
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(_original_activities))


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9
    assert "Chess Club" in data
    assert "Robotics Club" in data


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post("/activities/Chess Club/signup?email=new@mergington.edu")
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@mergington.edu for Chess Club"}
    # Confirm the email was actually added to in-memory state
    assert "new@mergington.edu" in app_module.activities["Chess Club"]["participants"]


def test_signup_duplicate_returns_400():
    # michael@mergington.edu is already in Chess Club (initial data)
    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_unknown_activity_returns_404():
    response = client.post("/activities/Unknown Activity/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    response = client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.status_code == 200
    assert response.json() == {"message": "Unregistered michael@mergington.edu from Chess Club"}
    # Confirm the email was actually removed from in-memory state
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]


def test_unregister_not_enrolled_returns_404():
    response = client.delete("/activities/Chess Club/signup?email=nothere@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_unknown_activity_returns_404():
    response = client.delete("/activities/Unknown Activity/signup?email=michael@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
