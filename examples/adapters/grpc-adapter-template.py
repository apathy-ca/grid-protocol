"""
GRID Protocol Adapter: gRPC Template

This template demonstrates how to create a GRID adapter for gRPC services.
It translates gRPC requests/responses to/from GRID's universal format.

Use this template for:
- Service mesh governance
- Internal service communication
- High-performance RPC governance
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime
import grpc
import jwt

# Assume these are imported from a GRID SDK
from .http_adapter_template import (
    Principal, Resource, Action, Context, GridRequest, GridResponse, ProtocolAdapter
)


# =============================================================================
# gRPC-Specific Types
# =============================================================================

@dataclass
class gRPCRequest:
    """gRPC request representation"""
    service_name: str
    method_name: str
    request_message: Any
    context: grpc.ServicerContext


@dataclass
class gRPCResponse:
    """gRPC response representation"""
    response_message: Any
    trailing_metadata: Optional[Dict[str, str]] = None


# =============================================================================
# gRPC Adapter Implementation
# =============================================================================

class gRPCAdapter(ProtocolAdapter):
    """
    GRID adapter for gRPC services.

    Maps gRPC concepts to GRID abstractions:
    - gRPC service/method -> GRID Resource
    - gRPC metadata -> Principal
    - gRPC request message -> Action parameters
    """

    def __init__(self, jwt_secret: str, resource_registry: Dict[str, Resource]):
        self.jwt_secret = jwt_secret
        self.resource_registry = resource_registry
        self._principal_cache = {}

    def translate_request(self, grpc_request: gRPCRequest) -> GridRequest:
        """Translate gRPC request to GRID format."""
        principal = self.get_principal(grpc_request.context)
        
        resource_id = f"grpc-{grpc_request.service_name}/{grpc_request.method_name}"
        resource = self.resource_registry.get(resource_id, Resource(
            id=resource_id,
            type='service',
            name=f"{grpc_request.service_name}/{grpc_request.method_name}",
            sensitivity='medium'
        ))

        action = Action(
            operation='execute',
            parameters=self._message_to_dict(grpc_request.request_message)
        )

        context = Context(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            ip_address=grpc_request.context.peer(),
            metadata={
                'protocol': 'grpc',
                'service': grpc_request.service_name,
                'method': grpc_request.method_name,
            }
        )

        return GridRequest(
            principal=principal,
            resource=resource,
            action=action,
            context=context
        )

    def translate_response(self, grid_response: GridResponse, 
                          error: Optional[str] = None) -> grpc.ServicerContext:
        """Translate GRID response to gRPC context for termination."""
        if error:
            return self._abort_grpc_context(
                grpc.StatusCode.INTERNAL,
                f"Internal server error: {error}"
            )

        if not grid_response.allowed:
            return self._abort_grpc_context(
                grpc.StatusCode.PERMISSION_DENIED,
                f"Access denied: {grid_response.reason}"
            )
        
        # If allowed, the interceptor will just return the handler's result.
        # This method is primarily for aborting the call.
        # We can't construct a full response here as the handler hasn't run yet.
        return None # Indicates success, proceed with handler

    def get_principal(self, context: grpc.ServicerContext) -> Principal:
        """Extract principal from gRPC metadata."""
        metadata = dict(context.invocation_metadata())
        auth_header = metadata.get('authorization', '')

        if auth_header in self._principal_cache:
            return self._principal_cache[auth_header]

        if not auth_header.startswith('Bearer '):
            raise ValueError("Missing or invalid Bearer token in gRPC metadata")

        token = auth_header[7:]
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            principal = Principal(
                id=payload['sub'],
                type=payload.get('type', 'service'),
                role=payload.get('role'),
                teams=payload.get('teams', []),
                attributes=payload.get('attributes', {})
            )
            self._principal_cache[auth_header] = principal
            return principal
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid JWT token: {e}")

    def register_resource(self, grpc_service: Dict[str, Any]) -> Resource:
        """Register gRPC service method as a GRID resource."""
        resource_id = f"grpc-{grpc_service['service']}/{grpc_service['method']}"
        return Resource(
            id=resource_id,
            type='service',
            name=f"{grpc_service['service']}/{grpc_service['method']}",
            sensitivity=grpc_service.get('sensitivity', 'medium'),
            owner=grpc_service.get('owner')
        )

    def _message_to_dict(self, message: Any) -> Dict:
        """Convert gRPC message to a dictionary."""
        from google.protobuf.json_format import MessageToDict
        return MessageToDict(message, preserving_proto_field_name=True)

    def _abort_grpc_context(self, code: grpc.StatusCode, details: str) -> grpc.ServicerContext:
        """Helper to abort a gRPC context."""
        class AbortContext:
            def abort(self, code, details):
                self._code = code
                self._details = details
                raise grpc.RpcError() # This is a simplification
        
        context = AbortContext()
        context.abort(code, details)
        return context # In a real interceptor, you'd call context.abort()

# =============================================================================
# Usage Example (in a gRPC Interceptor)
# =============================================================================

class GridInterceptor(grpc.ServerInterceptor):
    def __init__(self, adapter: gRPCAdapter):
        self._adapter = adapter

    def intercept_service(self, continuation, handler_call_details):
        service_name = handler_call_details.method.split('/')[1]
        method_name = handler_call_details.method.split('/')[2]

        def grid_wrapper(request, context):
            grpc_request = gRPCRequest(
                service_name=service_name,
                method_name=method_name,
                request_message=request,
                context=context
            )

            try:
                # 1. Translate and evaluate
                grid_request = self._adapter.translate_request(grpc_request)
                
                # This would be a call to the GRID policy engine
                # grid_response = policy_engine.evaluate(grid_request)
                # For this example, we'll simulate a response.
                grid_response = GridResponse(allowed=True, reason="Policy allows access")

                # 2. Translate response (check for denial)
                abort_context = self._adapter.translate_response(grid_response)
                if abort_context:
                    return # The context would have been aborted

                # 3. If allowed, continue to the actual gRPC method handler
                return continuation(request, context)

            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"GRID Interceptor Error: {e}")

        # This is a simplification of how interceptors work.
        # The actual implementation is more complex.
        # This demonstrates the logic flow.
        
        # We would replace the handler with our wrapper
        # return grpc.unary_unary_rpc_method_handler(
        #     grid_wrapper,
        #     request_deserializer=...,
        #     response_serializer=...
        # )
        return continuation(handler_call_details)


if __name__ == '__main__':
    # This is a conceptual example. A real implementation would involve
    # setting up a gRPC server with the interceptor.
    
    print("gRPC Adapter Template")
    print("This file should be used to build a gRPC server interceptor.")

    # 1. Initialize adapter
    resource_registry = {
        'grpc-MyService/MyMethod': Resource(
            id='grpc-MyService/MyMethod',
            type='service',
            name='MyService/MyMethod',
            sensitivity='high'
        )
    }
    adapter = gRPCAdapter(jwt_secret='your-secret-key', resource_registry=resource_registry)

    # 2. Create interceptor
    interceptor = GridInterceptor(adapter)

    # 3. Add interceptor to gRPC server
    # server = grpc.server(
    #     futures.ThreadPoolExecutor(max_workers=10),
    #     interceptors=(interceptor,)
    # )
    
    print("Conceptual setup complete.")