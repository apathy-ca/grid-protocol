# GRID Migration Tools

This directory contains tools to help you migrate your existing authorization policies and data to the GRID protocol.

## Goal

The goal of these tools is to automate as much of the migration process as possible, reducing the manual effort and potential for error.

## Planned Tools

### 1. Policy Converters

These scripts will convert policies from common authorization systems into the Rego format used by GRID.

-   **AWS IAM to Rego:** A tool to convert AWS IAM policies to GRID policies.
-   **Azure RBAC to Rego:** A tool to convert Azure RBAC roles and assignments to GRID policies.
-   **Custom CSV to Rego:** A generic tool to convert a CSV file of roles and permissions into a GRID policy.

### 2. Data Importers

These scripts will help you import your existing user and resource data into a format that can be used by GRID.

-   **LDAP to JSON:** A tool to export users and groups from an LDAP directory to a JSON file.
-   **SQL to JSON:** A tool to export user and resource data from a SQL database to a JSON file.

## How to Use

Each tool will have its own documentation explaining how to use it. The general process will be:

1.  Export your data from your existing system.
2.  Run the appropriate conversion or import tool.
3.  Review and refine the generated policies and data.
4.  Deploy your new GRID-based authorization system.

## Contributing

We welcome contributions to these tools. If you have a system you would like to see a migration tool for, please open an issue or submit a pull request.