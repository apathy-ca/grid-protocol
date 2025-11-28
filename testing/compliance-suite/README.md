# GRID Compliance Test Suite

This suite contains a series of tests to verify that a GRID implementation correctly adheres to the GRID protocol specification. Running these tests is a critical step for any new implementation to ensure it is compliant and interoperable with the GRID ecosystem.

## Running the Tests

The compliance tests are written in Python using the `pytest` framework. To run the tests, you will need to have a running GRID-compliant server.

1.  **Install dependencies:**
    ```bash
    pip install pytest requests
    ```

2.  **Configure the test suite:**
    Set the `GRID_SERVER_URL` environment variable to point to your GRID server.
    ```bash
    export GRID_SERVER_URL="http://localhost:8080"
    ```

3.  **Run the tests:**
    ```bash
    pytest
    ```

## Test Structure

The tests are organized by the different areas of the GRID specification:

-   `test_authorization.py`: Tests for the core authorization endpoints.
-   `test_policy_management.py`: Tests for the policy management APIs.
-   `test_audit.py`: Tests for the audit logging functionality.

Each test file contains a series of tests for a specific part of the specification. The tests make requests to the GRID server and assert that the responses are correct according to the spec.