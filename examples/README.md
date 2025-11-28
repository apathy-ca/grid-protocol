# GRID Protocol Examples

This directory contains practical examples for implementing and using GRID governance.

## Directory Structure

```
examples/
├── policies/          # Policy examples in Rego
├── adapters/          # Protocol adapter templates
├── integrations/      # Deployment examples
└── use-cases/         # Real-world scenarios
```

## Quick Start

### 1. Policy Examples
Start with basic RBAC policies and progress to advanced scenarios:
- [`policies/rbac-basic.rego`](policies/rbac-basic.rego) - Simple role-based access
- [`policies/rbac-team-based.rego`](policies/rbac-team-based.rego) - Team membership
- [`policies/abac-sensitivity.rego`](policies/abac-sensitivity.rego) - Attribute-based
- [`policies/time-based-access.rego`](policies/time-based-access.rego) - Temporal restrictions

### 2. Protocol Adapters
Templates for creating custom protocol adapters:
- [`adapters/http-adapter-template.py`](adapters/http-adapter-template.py) - REST/HTTP
- [`adapters/grpc-adapter-template.py`](adapters/grpc-adapter-template.py) - gRPC services
- [`adapters/custom-adapter-template.py`](adapters/custom-adapter-template.py) - Custom protocols

### 3. Deployment Examples
Production-ready deployment configurations:
- [`integrations/kubernetes/`](integrations/kubernetes/) - K8s manifests
- [`integrations/docker/`](integrations/docker/) - Docker Compose
- [`integrations/terraform/`](integrations/terraform/) - Infrastructure as Code

### 4. Use Cases
Real-world governance scenarios:
- [`use-cases/ai-agent-governance.md`](use-cases/ai-agent-governance.md) - AI/LLM tools
- [`use-cases/microservices-governance.md`](use-cases/microservices-governance.md) - Service mesh
- [`use-cases/iot-governance.md`](use-cases/iot-governance.md) - IoT devices

## Testing Examples

All policy examples can be tested with OPA:

```bash
# Install OPA
brew install opa  # macOS
# or download from https://www.openpolicyagent.org/

# Test a policy
opa test examples/policies/rbac-basic.rego

# Evaluate a policy
opa eval -d examples/policies/rbac-basic.rego \
  -i test-input.json \
  "data.grid.authorization.allow"
```

## Contributing Examples

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing new examples.

---

**Need help?** See the [main README](../README.md) or [QUICKSTART](../QUICKSTART.md)