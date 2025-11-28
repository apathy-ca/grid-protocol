# Docker Integration Test Example

This example demonstrates how to conduct integration testing for a GRID-enabled application using Docker Compose.

## Overview

This test setup consists of three services:
1.  `grid-server`: A mock GRID server, using the official Open Policy Agent image.
2.  `app`: A simple Python application that makes authorization requests to the GRID server before performing an action.
3.  `tests`: A `pytest` container that runs integration tests against the `app` service.

## How to Run

1.  **Build and run the services:**
    ```bash
    docker-compose up --build
    ```

2.  **View test results:**
    The output from the `tests` container will show the results of the integration tests. A successful run will exit with code 0.

## Test Scenario

The tests verify that the `app` service correctly communicates with the `grid-server` and enforces the authorization policies.