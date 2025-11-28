# GRID Protocol Adapter Examples

This directory contains template implementations for creating GRID protocol adapters.

## What is a Protocol Adapter?

A protocol adapter translates between a specific protocol (HTTP, gRPC, MCP, etc.) and GRID's universal governance abstractions. This allows GRID to govern any type of machine-to-machine interaction.

## Architecture

```
Protocol-Specific Request
        ↓
Protocol Adapter (translates)
        ↓
GRID Universal Format
        ↓
Policy Evaluation
        ↓
GRID Decision
        ↓
Protocol Adapter (translates back)
        ↓
Protocol-Specific Response
```

## Available Templates

### 1. HTTP/REST Adapter
**File:** [`http-adapter-template.py`](http-adapter-template.py)

Governs REST APIs and HTTP services:
- Maps HTTP methods to GRID actions
- Extracts principals from Authorization headers
- Translates HTTP responses

**Use cases:**
- REST API governance
- Microservice-to-microservice calls
- Web service access control

### 2. gRPC Adapter
**File:** [`grpc-adapter-template.py`](grpc-adapter-template.py)

Governs gRPC service calls:
- Maps gRPC methods to GRID actions
- Extracts principals from metadata/mTLS
- Handles streaming RPCs

**Use cases:**
- Service mesh governance
- Internal service communication
- High-performance RPC governance

### 3. Custom Protocol Adapter
**File:** [`custom-adapter-template.py`](custom-adapter-template.py)

Template for any custom protocol:
- Abstract base class implementation
- Extensible for proprietary protocols
- Complete example structure

**Use cases:**
- Proprietary protocols
- Legacy system integration
- Custom RPC frameworks

## Adapter Interface

All adapters must implement the `ProtocolAdapter` interface:

```python
class ProtocolAdapter(ABC):
    @abstractmethod
    def translate_request(self, protocol_request) -> GridRequest:
        """Translate protocol-specific request to GRID format"""
        pass
    
    @abstractmethod
    def translate_response(self, grid_response) -> ProtocolResponse:
        """Translate GRID response back to protocol format"""
        pass
    
    @abstractmethod
    def get_principal(self, protocol_context) -> Principal:
        """Extract principal from protocol context"""
        pass
    
    @abstractmethod
    def register_resource(self, protocol_resource) -> Resource:
        """Register protocol-specific resource in GRID"""
        pass
```

## Creating Your Own Adapter

### Step 1: Choose a Template
Start with the template closest to your protocol:
- HTTP-like protocols → Use HTTP adapter template
- RPC-like protocols → Use gRPC adapter template
- Unique protocols → Use custom adapter template

### Step 2: Implement Required Methods
```python
class MyProtocolAdapter(ProtocolAdapter):
    def translate_request(self, my_request):
        return GridRequest(
            principal=self._extract_principal(my_request),
            resource=self._extract_resource(my_request),
            action=self._extract_action(my_request),
            context=self._extract_context(my_request)
        )
    
    # Implement other methods...
```

### Step 3: Test Your Adapter
```python
# Test with sample requests
adapter = MyProtocolAdapter()
grid_request = adapter.translate_request(sample_request)
assert grid_request.principal.id is not None
assert grid_request.resource.id is not None
```

### Step 4: Integrate with GRID
```python
# Register adapter with GRID
grid_gateway.register_adapter("my-protocol", MyProtocolAdapter())

# Use adapter
response = grid_gateway.evaluate(my_protocol_request)
```

## Testing Adapters

### Unit Tests
```python
import unittest

class TestMyAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = MyProtocolAdapter()
    
    def test_translate_request(self):
        request = create_sample_request()
        grid_request = self.adapter.translate_request(request)
        self.assertIsNotNone(grid_request.principal)
    
    def test_translate_response(self):
        grid_response = create_sample_response()
        response = self.adapter.translate_response(grid_response)
        self.assertEqual(response.status, 200)
```

### Integration Tests
```python
def test_end_to_end():
    # Create adapter
    adapter = MyProtocolAdapter()
    
    # Create request
    request = create_protocol_request()
    
    # Translate to GRID
    grid_request = adapter.translate_request(request)
    
    # Evaluate policy
    decision = policy_engine.evaluate(grid_request)
    
    # Translate back
    response = adapter.translate_response(decision)
    
    assert response.allowed == True
```

## Best Practices

### 1. Principal Extraction
Always validate and sanitize principal information:
```python
def get_principal(self, context):
    # Validate token
    token = self._validate_token(context.auth_header)
    
    # Extract claims
    claims = self._decode_token(token)
    
    # Create principal
    return Principal(
        id=claims['sub'],
        type=claims.get('type', 'human'),
        attributes=claims.get('attributes', {})
    )
```

### 2. Error Handling
Provide clear error messages:
```python
def translate_request(self, request):
    try:
        return GridRequest(...)
    except KeyError as e:
        raise AdapterError(f"Missing required field: {e}")
    except Exception as e:
        raise AdapterError(f"Translation failed: {e}")
```

### 3. Context Preservation
Preserve protocol-specific context:
```python
def translate_request(self, request):
    return GridRequest(
        # ... standard fields ...
        context={
            'protocol': 'my-protocol',
            'protocol_version': request.version,
            'original_headers': request.headers,
            # ... other protocol-specific data ...
        }
    )
```

### 4. Performance
Cache expensive operations:
```python
class MyAdapter(ProtocolAdapter):
    def __init__(self):
        self._principal_cache = {}
    
    def get_principal(self, context):
        cache_key = context.auth_token
        if cache_key in self._principal_cache:
            return self._principal_cache[cache_key]
        
        principal = self._extract_principal(context)
        self._principal_cache[cache_key] = principal
        return principal
```

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on contributing adapter templates.

## Resources

- [GRID Protocol Specification](../../GRID_PROTOCOL_SPECIFICATION_v0.1.md) §9 - Protocol Adapters
- [SARK MCP Adapter](https://github.com/anthropics/sark) - Reference implementation
- [Gap Analysis](../../GRID_GAP_ANALYSIS_AND_IMPLEMENTATION_NOTES.md) §6 - Protocol Abstraction

---

**Questions?** Open an issue or see the [main README](../../README.md)