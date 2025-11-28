# Kubernetes Integration Test Example

This example demonstrates how to conduct integration testing for a GRID-enabled application in a Kubernetes environment.

## Overview

This test setup uses `minikube` for a local Kubernetes cluster and deploys:
1.  `grid-server`: A GRID server (OPA) as a Kubernetes service.
2.  `app`: A simple Python application that queries the `grid-server`.
3.  `tests`: A Kubernetes Job that runs `pytest` to test the application's authorization logic.

## How to Run

1.  **Start a local Kubernetes cluster:**
    ```bash
    minikube start
    ```

2.  **Apply the Kubernetes manifests:**
    ```bash
    kubectl apply -f .
    ```

3.  **View test results:**
    Check the logs of the test pod to see the results.
    ```bash
    kubectl logs -l app=grid-test
    ```
    A successful run will show "PASSED" in the logs.

## Building Local Images

Before applying the manifest, you need to build the `grid-app` and `grid-test` Docker images and load them into your `minikube` environment. You can reuse the `Dockerfile` and application code from the `docker` example.

1.  **Point your Docker client to minikube's Docker daemon:**
    ```bash
    eval $(minikube docker-env)
    ```

2.  **Build the images:**
    ```bash
    docker build -t grid-app:latest ../docker/app
    docker build -t grid-test:latest ../docker/tests
    ```

## Cleanup

```bash
kubectl delete -f .
minikube stop