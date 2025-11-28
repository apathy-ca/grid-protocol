# GRID Docker Integration Examples

This directory contains examples of how to deploy and configure GRID using Docker Compose.

## Examples

- **[docker-compose.yml](docker-compose.yml):** A sample Docker Compose file for a GRID gateway (e.g., SARK) and its dependencies.

## Deployment

To deploy these examples using Docker Compose:

```bash
# Start the services
docker-compose -f examples/integrations/docker/docker-compose.yml up -d
```

## Configuration

The `docker-compose.yml` file includes a sample configuration for a GRID gateway and its dependencies, including:

- **GRID Gateway:** The main GRID service (e.g., SARK).
- **OPA:** The Open Policy Agent policy engine.
- **PostgreSQL:** The database for the audit log.
- **Redis:** The cache for policy decisions.

You will need to customize this configuration for your environment.