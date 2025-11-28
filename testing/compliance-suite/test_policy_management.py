import os
import requests
import pytest
import base64

# Get the GRID server URL from an environment variable
GRID_SERVER_URL = os.environ.get("GRID_SERVER_URL", "http://localhost:8080")

POLICY_ID = "com.grid.test.policy"
POLICY_CONTENT = "package grid.authz\n\ndefault allow = false"
ENCODED_POLICY_CONTENT = base64.b64encode(POLICY_CONTENT.encode()).decode()

@pytest.fixture(scope="module")
def setup_policy():
    """A fixture to create a policy and clean it up after tests."""
    # Create a policy to be used by other tests
    url = f"{GRID_SERVER_URL}/v1/policies/{POLICY_ID}"
    payload = {"policy": ENCODED_POLICY_CONTENT}
    response = requests.put(url, json=payload)
    assert response.status_code in [200, 201]
    
    yield
    
    # Cleanup: delete the policy
    response = requests.delete(url)
    assert response.status_code in [204, 404]

def test_create_policy():
    """
    Test creating a new policy.
    """
    policy_id = "com.grid.test.create"
    url = f"{GRID_SERVER_URL}/v1/policies/{policy_id}"
    payload = {"policy": ENCODED_POLICY_CONTENT}
    
    # Ensure policy doesn't exist
    requests.delete(url)
    
    response = requests.put(url, json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == policy_id

    # Clean up
    requests.delete(url)

def test_get_policy(setup_policy):
    """
    Test retrieving a policy.
    """
    url = f"{GRID_SERVER_URL}/v1/policies/{POLICY_ID}"
    response = requests.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == POLICY_ID
    assert data["policy"] == ENCODED_POLICY_CONTENT

def test_update_policy(setup_policy):
    """
    Test updating a policy.
    """
    url = f"{GRID_SERVER_URL}/v1/policies/{POLICY_ID}"
    updated_content = "package grid.authz\n\ndefault allow = true"
    encoded_updated_content = base64.b64encode(updated_content.encode()).decode()
    payload = {"policy": encoded_updated_content}
    
    response = requests.put(url, json=payload)
    assert response.status_code == 200
    
    # Verify the update
    get_response = requests.get(url)
    assert get_response.status_code == 200
    assert get_response.json()["policy"] == encoded_updated_content

def test_delete_policy():
    """
    Test deleting a policy.
    """
    policy_id = "com.grid.test.delete"
    url = f"{GRID_SERVER_URL}/v1/policies/{policy_id}"
    payload = {"policy": ENCODED_POLICY_CONTENT}

    # Create policy to delete
    requests.put(url, json=payload)

    response = requests.delete(url)
    assert response.status_code == 204

    # Verify deletion
    get_response = requests.get(url)
    assert get_response.status_code == 404