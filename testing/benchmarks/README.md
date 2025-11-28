# GRID Performance Benchmarks

This directory contains tools and procedures for measuring the performance of GRID components.

For a detailed explanation of the benchmarking process, see [BENCHMARKING_PROCESS.md](BENCHMARKING_PROCESS.md).

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Locust:**
    Start the Locust web interface, pointing it to your GRID server.
    ```bash
    locust -f locustfile.py --host http://localhost:8080
    ```

3.  **Start the load test:**
    Open your browser to `http://localhost:8089` and start a new load test.

## Scenarios

The `locustfile.py` contains several user scenarios to simulate different types of traffic:
-   `authorize_endpoint`: A standard authorization request from a "viewer" user.
-   `authorize_admin`: A request from an "admin" user, which may have a different performance profile.