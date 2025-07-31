"""
Auth Middleware Node for Theo Authentication System

Cookbook Reference: pocketflow-fastapi-background

PocketFlow Node implementing authentication middleware with role-based access control,
JWT token validation, and proper HTTP status code handling.
Estimated Lines: 145/150
"""

from pocketflow import AsyncNode
from typing import Dict, Any, List
from .jwt_validation_node import JWTValidationNode


class AuthMiddlewareNode(AsyncNode):
    """
    Authentication middleware with role-based access control
    
    Cookbook Reference: pocketflow-fastapi-background
    
    Validates JWT tokens and enforces user permissions based on role hierarchy.
    Supports flexible role requirements and proper HTTP status codes.
    """
    
    def __init__(self):
        super().__init__()
        self.jwt_validator = JWTValidationNode()
        # Role hierarchy: admin inherits user permissions
        self.role_hierarchy = {
            "admin": ["admin", "user"],  # Admin has all permissions
            "user": ["user"]             # User has basic permissions only
        }
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Main authentication middleware logic"""
        try:
            # Extract authentication requirements
            required_roles = shared_store.get("required_roles", [])
            authorization_header = shared_store.get("authorization_header")
            
            # Check if authorization header is present
            if not authorization_header:
                return self._auth_error("Authorization header missing", 401)
            
            # Validate JWT token
            validation_result = await self._validate_token(authorization_header)
            
            if not validation_result["valid"]:
                return self._auth_error(validation_result["error"], 401)
            
            # Check role requirements if specified
            user_role = validation_result["role"]
            if required_roles and not self._check_role_access(user_role, required_roles):
                return self._auth_error(
                    f"Insufficient permissions. Required: {', '.join(required_roles)}", 403
                )
            
            # Authentication successful
            return {
                "authenticated": True,
                "user_id": validation_result["user_id"],
                "email": validation_result["email"],
                "role": validation_result["role"],
                "status_code": 200
            }
            
        except Exception as e:
            return self._auth_error(f"Authentication failed: {str(e)}", 500)
    
    async def _validate_token(self, authorization_header: str) -> Dict[str, Any]:
        """Validate JWT token using JWTValidationNode"""
        result = await self.jwt_validator.run({
            "token": authorization_header
        })
        return result
    
    def _check_role_access(self, user_role: str, required_roles: List[str]) -> bool:
        """Check if user role has required permissions"""
        user_permissions = self.role_hierarchy.get(user_role, [])
        return any(role in user_permissions for role in required_roles)
    
    def _auth_error(self, error_message: str, status_code: int) -> Dict[str, Any]:
        """Standard authentication error response"""
        return {
            "authenticated": False,
            "error": error_message,
            "status_code": status_code
        }