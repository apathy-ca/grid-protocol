"""
GRID Protocol Adapter: Custom Protocol Template

This template provides a skeleton for creating a GRID adapter for any
proprietary or custom protocol.

Use this template for:
- Proprietary RPC frameworks
- Legacy system integration
- Custom messaging protocols (e.g., over sockets, message queues)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime

# Assume these are imported from a GRID SDK
from .http_adapter_template import (
    Principal, Resource, Action, Context, GridRequest, GridResponse, ProtocolAdapter
)


# =============================================================================
# Custom Protocol-Specific Types (Replace with your protocol's types)
# =============================================================================

@dataclass
class CustomProtocolRequest:
    """Your custom protocol's request representation."""
    header: Dict[str, Any]
    payload: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class CustomProtocolResponse:
    """Your custom protocol's response representation."""
    status_code: int
    status_message: str
    data: Optional[Dict[str, Any]] = None


# =============================================================================
# Custom Adapter Implementation
# =============================================================================

class CustomAdapter(ProtocolAdapter):
    """
    GRID adapter for a custom protocol.

    You need to implement the logic to map your protocol's concepts
    to GRID's universal abstractions.
    """

    def __init__(self, resource_registry: Dict[str, Resource]):
        self.resource_registry = resource_registry

    def translate_request(self, custom_request: CustomProtocolRequest) -> GridRequest:
        """Translate your custom protocol request to the GRID format."""
        
        # 1. Extract Principal
        # This logic will be highly specific to your protocol's auth mechanism.
        # e.g., from a token in the header, a session ID, etc.
        principal = self.get_principal(custom_request)

        # 2. Identify Resource
        # Determine what is being accessed from the request payload.
        resource_id = custom_request.payload.get('target_resource')
        if not resource_id:
            raise ValueError("Could not identify resource from request")
        
        resource = self.resource_registry.get(resource_id, Resource(
            id=resource_id,
            type='custom-service',
            name=resource_id,
            sensitivity='medium'
        ))

        # 3. Define Action
        # Map the operation in your protocol to a GRID action.
        operation = custom_request.payload.get('operation')
        if not operation:
            raise ValueError("Could not identify operation from request")

        action = Action(
            operation=self._map_custom_op_to_grid_action(operation),
            parameters=custom_request.payload.get('params', {})
        )

        # 4. Build Context
        context = Context(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            ip_address=custom_request.metadata.get('source_ip'),
            request_id=custom_request.header.get('request_id'),
            metadata={
                'protocol': 'custom',
                'custom_header': custom_request.header,
            }
        )

        return GridRequest(
            principal=principal,
            resource=resource,
            action=action,
            context=context
        )

    def translate_response(self, grid_response: GridResponse, 
                          error: Optional[str] = None) -> CustomProtocolResponse:
        """Translate a GRID decision back to your custom protocol's response format."""
        if error:
            return CustomProtocolResponse(
                status_code=500,
                status_message="Internal GRID Error",
                data={'error_details': error}
            )

        if not grid_response.allowed:
            return CustomProtocolResponse(
                status_code=403,
                status_message="Access Denied",
                data={
                    'reason': grid_response.reason,
                    'policy_id': grid_response.policy_id
                }
            )

        return CustomProtocolResponse(
            status_code=200,
            status_message="Success",
            data=grid_response.data or {}
        )

    def get_principal(self, custom_request: CustomProtocolRequest) -> Principal:
        """Extract the principal from your custom request."""
        
        # This is a placeholder. Your logic will depend on your auth system.
        # For example, you might decode a custom token.
        auth_token = custom_request.header.get('X-Auth-Token')
        if not auth_token:
            raise ValueError("Authentication token is missing")

        # Here you would have logic to validate the token and get user info.
        # For this example, we'll use a dummy implementation.
        user_id = f"user_from_token_{auth_token}"
        
        return Principal(
            id=user_id,
            type='human',
            role='user', # You would get this from your user system
            attributes={'source_token': auth_token}
        )

    def register_resource(self, custom_resource: Dict[str, Any]) -> Resource:
        """Register a resource from your custom protocol."""
        resource_id = custom_resource.get('id')
        if not resource_id:
            raise ValueError("Resource must have an ID")

        return Resource(
            id=resource_id,
            type='custom-service',
            name=custom_resource.get('name', resource_id),
            sensitivity=custom_resource.get('sensitivity', 'medium'),
            owner=custom_resource.get('owner')
        )

    def _map_custom_op_to_grid_action(self, custom_op: str) -> str:
        """Map your protocol's operations to standard GRID actions."""
        op_map = {
            'GET_DATA': 'read',
            'FETCH': 'read',
            'UPDATE_DATA': 'write',
            'SAVE': 'write',
            'RUN_COMMAND': 'execute',
            'TRIGGER': 'execute',
            'DELETE_DATA': 'write', # or a custom 'delete' action
        }
        return op_map.get(custom_op.upper(), 'execute')


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == '__main__':
    print("Custom Protocol Adapter Template")

    # 1. Initialize adapter with known resources
    resource_registry = {
        'legacy_db_1': Resource(
            id='legacy_db_1',
            type='custom-service',
            name='Legacy Customer Database',
            sensitivity='high'
        )
    }
    adapter = CustomAdapter(resource_registry=resource_registry)

    # 2. Simulate an incoming request from your custom protocol
    incoming_request = CustomProtocolRequest(
        header={
            'X-Auth-Token': 'abc-123',
            'request_id': 'xyz-789'
        },
        payload={
            'target_resource': 'legacy_db_1',
            'operation': 'GET_DATA',
            'params': {'customer_id': 42}
        },
        metadata={
            'source_ip': '192.168.1.100'
        }
    )
    print(f"\nSimulating incoming request: {incoming_request}")

    # 3. Translate to GRID format
    try:
        grid_request = adapter.translate_request(incoming_request)
        print(f"\nTranslated to GRID format: {grid_request}")

        # 4. Simulate a policy engine decision (in a real system, you'd call GRID)
        # Let's simulate a DENIED decision
        grid_decision = GridResponse(
            allowed=False,
            reason="Access to high sensitivity data requires admin role",
            policy_id="policy-abac-1"
        )
        print(f"\nSimulating GRID decision: {grid_decision}")

        # 5. Translate the decision back to your protocol's format
        custom_response = adapter.translate_response(grid_decision)
        print(f"\nTranslated back to custom protocol response: {custom_response}")
        assert custom_response.status_code == 403

        # Now simulate an ALLOWED decision
        grid_decision_allowed = GridResponse(
            allowed=True,
            reason="Policy allows read access",
            policy_id="policy-rbac-2",
            data={'customer_name': 'John Doe', 'email': 'john.doe@example.com'}
        )
        print(f"\nSimulating GRID decision: {grid_decision_allowed}")
        custom_response_allowed = adapter.translate_response(grid_decision_allowed)
        print(f"\nTranslated back to custom protocol response: {custom_response_allowed}")
        assert custom_response_allowed.status_code == 200
        assert custom_response_allowed.data['customer_name'] == 'John Doe'

    except ValueError as e:
        print(f"\nError during translation: {e}")