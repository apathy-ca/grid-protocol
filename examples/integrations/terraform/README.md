# GRID Terraform Integration Examples

This directory contains examples of how to deploy and configure GRID using Terraform.

## Examples

- **[main.tf](main.tf):** A sample Terraform configuration for deploying a GRID gateway (e.g., SARK) and its dependencies to AWS.

## Deployment

To deploy these examples using Terraform:

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Plan the deployment:**
   ```bash
   terraform plan
   ```

3. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## Configuration

The `main.tf` file includes a sample configuration for deploying a GRID gateway and its dependencies to AWS, including:

- **VPC:** A virtual private cloud for the GRID deployment.
- **ECS Cluster:** An Elastic Container Service cluster for running the GRID gateway.
- **RDS Instance:** A Relational Database Service instance for the audit log.
- **ElastiCache Instance:** An ElastiCache instance for the policy cache.

You will need to customize this configuration for your environment.