# Terraform Integration Test Example

This example demonstrates how to use Terraform to provision infrastructure and run integration tests against a GRID-enabled application.

## Overview

This example uses Terraform to:
1.  Provision a Docker container running a mock `grid-server`.
2.  Provision a Docker container running the `app`.
3.  Run a third container with `pytest` to execute tests against the `app`.

This approach allows for testing the entire application stack as it would be deployed.

## How to Run

1.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

2.  **Apply the configuration:**
    ```bash
    terraform apply -auto-approve
    ```
    This will provision the containers and run the tests. The test runner container will exit with a non-zero status code if tests fail, causing the `terraform apply` command to fail.

3.  **View test results:**
    The output of the `terraform apply` command will include the logs from the test runner.

## Cleanup

```bash
terraform destroy -auto-approve