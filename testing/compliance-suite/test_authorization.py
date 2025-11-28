import os
import requests
import pytest

# Get the GRID server URL from an environment variable
GRID_SERVER_URL = os.environ.get("GRID_SERVER_URL", "http://localhost:8080")


def test_authorize_endpoint_returns_200():
    """
    Tests that the /authorize endpoint returns a 200 OK response for a valid request.
    """
    url = f"{GRID_SERVER_URL}/authorize"
    payload = {
        "principal": {"id": "user1", "role": "viewer"},
        "action": {"operation": "read"},
        "resource": {"id": "document/123", "sensitivity": "low"}
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200

def test_authorize_endpoint_denies_invalid_request():
    """
    Tests that the /authorize endpoint returns a decision of 'deny' for an invalid request.
    """
    url = f"{GRID_SERVER_URL}/authorize"
    payload = {
        "principal": {"id": "user1", "role": "viewer"},
        "action": {"operation": "write"},
        "resource": {"id": "document/123", "sensitivity": "high"}
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    decision = response.json()
    assert decision.get("allow") == False

def test_authorize_endpoint_returns_400_for_malformed_json():
    """
    Tests that the /authorize endpoint returns a 400 Bad Request for malformed JSON.
    """
    url = f"{GRID_SERVER_URL}/authorize"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data="{malformed json}", headers=headers)
    assert response.status_code == 400

@pytest.mark.parametrize("missing_field", ["principal", "action", "resource"])
def test_authorize_endpoint_returns_400_for_missing_field(missing_field):
    """
    Tests that the /authorize endpoint returns a 400 Bad Request if a required field is missing.
    """
    url = f"{GRID_SERVER_URL}/authorize"
    payload = {
        "principal": {"id": "user1", "role": "viewer"},
        "action": {"operation": "read"},
        "resource": {"id": "document/123", "sensitivity": "low"}
    }
    del payload[missing_field]
    response = requests.post(url, json=payload)
    assert response.status_code == 400

def test_authorize_endpoint_allows_valid_request():
    """
    Tests that the /authorize endpoint returns a decision of 'allow' for a valid request.
    """
    url = f"{GRID_SERVER_URL}/authorize"
    payload = {
        "principal": {"id": "admin", "role": "admin"},
        "action": {"operation": "write"},
        "resource": {"id": "document/123", "sensitivity": "high"}
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    decision = response.json()
    assert decision.get("allow") == True