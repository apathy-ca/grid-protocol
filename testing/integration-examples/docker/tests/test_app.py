import os
import requests

APP_URL = os.environ.get("APP_URL")

def test_access_granted_for_admin():
    """
    Tests that an admin user is granted access.
    """
    url = f"{APP_URL}/resource"
    payload = {"principal": {"role": "admin"}}
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Access granted"

def test_access_denied_for_viewer():
    """
    Tests that a viewer user is denied access.
    """
    url = f"{APP_URL}/resource"
    payload = {"principal": {"role": "viewer"}}
    response = requests.post(url, json=payload)
    assert response.status_code == 403
    assert response.json()["message"] == "Access denied"