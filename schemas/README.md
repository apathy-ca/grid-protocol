# GRID Protocol Schemas

This directory contains JSON schemas for the core GRID data structures, as well as an OpenAPI specification for the GRID API.

## Schemas

- **[audit-event.schema.json](audit-event.schema.json):** JSON schema for the audit event structure.
- **[policy.schema.json](policy.schema.json):** JSON schema for the policy structure.
- **[principal.schema.json](principal.schema.json):** JSON schema for the principal structure.
- **[resource.schema.json](resource.schema.json):** JSON schema for the resource structure.
- **[action.schema.json](action.schema.json):** JSON schema for the action structure.

## OpenAPI Specification

- **[openapi.yaml](openapi.yaml):** OpenAPI 3.0 specification for the GRID API.

## Usage

These schemas can be used to:

- Validate data structures in your GRID implementation.
- Generate client libraries for the GRID API.
- Power API documentation and testing tools.

### Validating with `ajv`

You can use a tool like `ajv-cli` to validate JSON data against the schemas:

```bash
# Install ajv-cli
npm install -g ajv-cli

# Validate an audit event
ajv validate -s schemas/audit-event.schema.json -d my-audit-event.json
```

### Using the OpenAPI Specification

You can use the OpenAPI specification with a variety of tools, such as:

- **[Swagger Editor](https://editor.swagger.io/):** Visualize and interact with the API.
- **[Swagger UI](https://swagger.io/tools/swagger-ui/):** Generate interactive API documentation.
- **[OpenAPI Generator](https://openapi-generator.tech/):** Generate client libraries in various languages.