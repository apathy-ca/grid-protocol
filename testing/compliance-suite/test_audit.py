import os
import requests
import pytest
from datetime import datetime, timedelta

# Get the GRID server URL from an environment variable
GRID_SERVER_URL = os.environ.get("GRID_SERVER_URL", "http://localhost:8080")

def test_log_event():
    """
    Test logging an audit event.
    """
    url = f"{GRID_SERVER_URL}/v1/audit"
    payload = {
        "principal": {"id": "user123"},
        "action": {"operation": "login"},
        "resource": {"id": "system"},
        "decision": "allow",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 202

def test_get_audit_logs():
    """
    Test retrieving audit logs.
    """
    # Log an event to ensure there's data
    test_log_event()

    url = f"{GRID_SERVER_URL}/v1/audit"
    
    # Give the server a moment to process the log
    import time
    time.sleep(1)

    # Retrieve logs for the last minute
    since = (datetime.utcnow() - timedelta(minutes=1)).isoformat() + "Z"
    params = {"since": since}
    
    response = requests.get(url, params=params)
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    
    # Check for expected fields in the first log entry
    log_entry = logs[0]
    assert "principal" in log_entry
    assert "action" in log_entry
    assert "resource" in log_entry
    assert "decision" in log_entry
    assert "timestamp" in log_entry