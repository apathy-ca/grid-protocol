"""
GRID Protocol Adapter: HTTP/REST Template

This template demonstrates how to create a GRID adapter for HTTP/REST APIs.
It translates HTTP requests/responses to/from GRID's universal format.

Use this template for:
- REST API governance
- Microservice-to-microservice calls
- Web service access control
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime
import jwt
import json


# =============================================================================
# GRID Core Types (would be imported from GRID SDK)
# =============================================================================

@dataclass
class Principal:
    """Who is making the request"""
    id: str
    type: str  # human, agent, service, device
    role: Optional[str] = None
    teams: Optional[list] = None
    attributes: Optional[Dict[str, Any]] = None


@dataclass
class Resource:
    """What is being accessed"""
    id: str
    type: str  # tool, data, service, device
    name: str
    sensitivity: str  # low, medium, high, critical
    owner: Optional[str] = None
    managers: Optional[list] = None


@dataclass
class Action:
    """What operation is being performed"""
    operation: str  # read, write, execute, control, manage, audit
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class Context:
    """Additional context about the request"""
    timestamp: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    environment: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GridRequest:
    """Universal GRID request format"""
    principal: Principal
    resource: Resource
    action: Action
    context: Context


@dataclass
class GridResponse:
    """Universal GRID response format"""
    allowed: bool
    reason: str
    policy_id: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None


# =============================================================================
# HTTP-Specific Types
# =============================================================================

@dataclass
class HTTPRequest:
    """HTTP request representation"""
    method: str  # GET, POST, PUT, DELETE, etc.
    path: str
    headers: Dict[str, str]
    body: Optional[Any] = None
    query_params: Optional[Dict[str, str]] = None
    remote_addr: Optional[str] = None


@dataclass
class HTTPResponse:
    """HTTP response representation"""
    status_code: int
    headers: Dict[str, str]
    body: Optional[Any] = None


# =============================================================================
# Protocol Adapter Interface
# =============================================================================

class ProtocolAdapter(ABC):
    """Abstract base class for protocol adapters"""
    
    @abstractmethod
    def translate_request(self, protocol_request: Any) -> GridRequest:
        """Translate protocol-specific request to GRID format"""
        pass
    
    @abstractmethod
    def translate_response(self, grid_response: GridResponse, 
                          error: Optional[str] = None) -> Any:
        """Translate GRID response back to protocol format"""
        pass
    
    @abstractmethod
    def get_principal(self, protocol_context: Any) -> Principal:
        """Extract principal from protocol context"""
        pass
    
    @abstractmethod
    def register_resource(self, protocol_resource: Any) -> Resource:
        """Register protocol-specific resource in GRID"""
        pass


# =============================================================================
# HTTP Adapter Implementation
# =============================================================================

class HTTPAdapter(ProtocolAdapter):
    """
    GRID adapter for HTTP/REST APIs
    
    Maps HTTP concepts to GRID abstractions:
    - HTTP methods → GRID actions
    - Authorization header → Principal
    - URL path → Resource
    - Request context → GRID context
    """
    
    def __init__(self, jwt_secret: str, resource_registry: Dict[str, Resource]):
        """
        Initialize HTTP adapter
        
        Args:
            jwt_secret: Secret for validating JWT tokens
            resource_registry: Map of URL paths to GRID resources
        """
        self.jwt_secret = jwt_secret
        self.resource_registry = resource_registry
        self._principal_cache = {}
    
    def translate_request(self, http_request: HTTPRequest) -> GridRequest:
        """
        Translate HTTP request to GRID format
        
        Args:
            http_request: HTTP request object
            
        Returns:
            GridRequest with GRID abstractions
            
        Example:
            HTTP: GET /api/users?id=123
            GRID: Principal=alice, Resource=/api/users, Action=read
        """
        # Extract principal from Authorization header
        principal = self.get_principal(http_request)
        
        # Map URL path to resource
        resource = self._get_resource_from_path(http_request.path)
        
        # Map HTTP method to GRID action
        action = self._map_http_method_to_action(
            http_request.method,
            http_request.body
        )
        
        # Build context
        context = Context(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            ip_address=http_request.remote_addr,
            user_agent=http_request.headers.get('User-Agent'),
            environment=self._detect_environment(http_request),
            request_id=http_request.headers.get('X-Request-ID'),
            metadata={
                'protocol': 'http',
                'method': http_request.method,
                'path': http_request.path,
                'query_params': http_request.query_params
            }
        )
        
        return GridRequest(
            principal=principal,
            resource=resource,
            action=action,
            context=context
        )
    
    def translate_response(self, grid_response: GridResponse,
                          error: Optional[str] = None) -> HTTPResponse:
        """
        Translate GRID response to HTTP format
        
        Args:
            grid_response: GRID decision
            error: Optional error message
            
        Returns:
            HTTPResponse with appropriate status code
        """
        if error:
            return HTTPResponse(
                status_code=500,
                headers={'Content-Type': 'application/json'},
                body={'error': 'Internal server error', 'message': error}
            )
        
        if not grid_response.allowed:
            return HTTPResponse(
                status_code=403,
                headers={'Content-Type': 'application/json'},
                body={
                    'error': 'Access denied',
                    'reason': grid_response.reason,
                    'policy_id': grid_response.policy_id
                }
            )
        
        # Apply rate limiting constraints if present
        headers = {'Content-Type': 'application/json'}
        if grid_response.constraints:
            if 'rate_limit' in grid_response.constraints:
                rl = grid_response.constraints['rate_limit']
                headers['X-RateLimit-Limit'] = str(rl.get('limit', ''))
                headers['X-RateLimit-Remaining'] = str(rl.get('remaining', ''))
                headers['X-RateLimit-Reset'] = str(rl.get('reset', ''))
        
        return HTTPResponse(
            status_code=200,
            headers=headers,
            body=grid_response.data or {'status': 'success'}
        )
    
    def get_principal(self, http_request: HTTPRequest) -> Principal:
        """
        Extract principal from HTTP Authorization header
        
        Supports:
        - Bearer tokens (JWT)
        - API keys
        - Basic auth
        
        Args:
            http_request: HTTP request
            
        Returns:
            Principal object
        """
        auth_header = http_request.headers.get('Authorization', '')
        
        # Check cache first
        if auth_header in self._principal_cache:
            return self._principal_cache[auth_header]
        
        principal = None
        
        # Bearer token (JWT)
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            principal = self._extract_principal_from_jwt(token)
        
        # API Key
        elif auth_header.startswith('ApiKey '):
            api_key = auth_header[7:]
            principal = self._extract_principal_from_api_key(api_key)
        
        # Basic auth
        elif auth_header.startswith('Basic '):
            principal = self._extract_principal_from_basic_auth(auth_header[6:])
        
        else:
            raise ValueError("No valid authentication provided")
        
        # Cache the principal
        self._principal_cache[auth_header] = principal
        return principal
    
    def register_resource(self, http_resource: Dict[str, Any]) -> Resource:
        """
        Register HTTP endpoint as GRID resource
        
        Args:
            http_resource: Dict with endpoint metadata
            
        Returns:
            Resource object
            
        Example:
            {
                "path": "/api/users",
                "methods": ["GET", "POST"],
                "sensitivity": "medium",
                "owner": "user-service-team"
            }
        """
        return Resource(
            id=f"http-{http_resource['path']}",
            type='service',
            name=http_resource['path'],
            sensitivity=http_resource.get('sensitivity', 'medium'),
            owner=http_resource.get('owner'),
            managers=http_resource.get('managers', [])
        )
    
    # =========================================================================
    # Private Helper Methods
    # =========================================================================
    
    def _extract_principal_from_jwt(self, token: str) -> Principal:
        """Extract principal from JWT token"""
        try:
            # Decode and validate JWT
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            return Principal(
                id=payload['sub'],
                type=payload.get('type', 'human'),
                role=payload.get('role'),
                teams=payload.get('teams', []),
                attributes=payload.get('attributes', {})
            )
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid JWT token: {e}")
    
    def _extract_principal_from_api_key(self, api_key: str) -> Principal:
        """Extract principal from API key (simplified example)"""
        # In production, look up API key in database
        # This is a simplified example
        return Principal(
            id=f"api-key-{api_key[:8]}",
            type='service',
            role='service',
            attributes={'api_key': api_key[:8]}
        )
    
    def _extract_principal_from_basic_auth(self, credentials: str) -> Principal:
        """Extract principal from Basic auth (simplified example)"""
        import base64
        decoded = base64.b64decode(credentials).decode('utf-8')
        username, _ = decoded.split(':', 1)
        
        return Principal(
            id=username,
            type='human',
            role='user'
        )
    
    def _get_resource_from_path(self, path: str) -> Resource:
        """Map URL path to GRID resource"""
        # Try exact match first
        if path in self.resource_registry:
            return self.resource_registry[path]
        
        # Try pattern matching (simplified)
        for pattern, resource in self.resource_registry.items():
            if self._path_matches_pattern(path, pattern):
                return resource
        
        # Default resource if not found
        return Resource(
            id=f"http-{path}",
            type='service',
            name=path,
            sensitivity='medium'
        )
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern (simplified)"""
        # Simple wildcard matching
        # In production, use proper regex or path matching library
        return pattern.replace('*', '') in path
    
    def _map_http_method_to_action(self, method: str, 
                                   body: Optional[Any]) -> Action:
        """Map HTTP method to GRID action"""
        method_map = {
            'GET': 'read',
            'HEAD': 'read',
            'POST': 'write',
            'PUT': 'write',
            'PATCH': 'write',
            'DELETE': 'write',
            'OPTIONS': 'read'
        }
        
        operation = method_map.get(method.upper(), 'execute')
        
        return Action(
            operation=operation,
            parameters=body if isinstance(body, dict) else {}
        )
    
    def _detect_environment(self, http_request: HTTPRequest) -> str:
        """Detect environment from request (simplified)"""
        host = http_request.headers.get('Host', '')
        
        if 'localhost' in host or '127.0.0.1' in host:
            return 'dev'
        elif 'staging' in host:
            return 'staging'
        else:
            return 'production'


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == '__main__':
    # Initialize adapter
    resource_registry = {
        '/api/users': Resource(
            id='users-api',
            type='service',
            name='Users API',
            sensitivity='medium',
            owner='backend-team'
        ),
        '/api/admin/*': Resource(
            id='admin-api',
            type='service',
            name='Admin API',
            sensitivity='critical',
            owner='admin-team'
        )
    }
    
    adapter = HTTPAdapter(
        jwt_secret='your-secret-key',
        resource_registry=resource_registry
    )
    
    # Example HTTP request
    http_request = HTTPRequest(
        method='GET',
        path='/api/users',
        headers={
            'Authorization': 'Bearer eyJ...',  # JWT token
            'User-Agent': 'MyApp/1.0',
            'X-Request-ID': 'req-123'
        },
        query_params={'id': '123'},
        remote_addr='10.1.2.3'
    )
    
    # Translate to GRID format
    grid_request = adapter.translate_request(http_request)
    print(f"Principal: {grid_request.principal.id}")
    print(f"Resource: {grid_request.resource.name}")
    print(f"Action: {grid_request.action.operation}")
    
    # Simulate GRID decision
    grid_response = GridResponse(
        allowed=True,
        reason="User has access to medium sensitivity resources",
        policy_id="rbac-default"
    )
    
    # Translate back to HTTP
    http_response = adapter.translate_response(grid_response)
    print(f"HTTP Status: {http_response.status_code}")
    print(f"Response: {http_response.body}")