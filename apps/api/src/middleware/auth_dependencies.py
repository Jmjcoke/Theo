"""
FastAPI Authentication Dependencies for Theo

Provides dependency functions for route protection with role-based access control.
Integrates with AuthMiddlewareNode for JWT validation and permission checking.
"""

from fastapi import Depends, HTTPException, Request
from typing import Dict, Any
from src.nodes.auth.auth_middleware_node import AuthMiddlewareNode

# Initialize the authentication middleware node
auth_middleware = AuthMiddlewareNode()


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user
    
    Validates JWT token and returns user information for any authenticated user.
    No specific role requirements.
    """
    authorization = request.headers.get("Authorization")
    
    shared_store = {
        "authorization_header": authorization,
        "required_roles": []  # No specific role required
    }
    
    result = await auth_middleware.run(shared_store)
    
    if not result["authenticated"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"]
        )
    
    return {
        "user_id": result["user_id"],
        "email": result["email"],
        "role": result["role"]
    }


async def require_user_role(request: Request) -> Dict[str, Any]:
    """
    Dependency requiring user or admin role
    
    Allows access to users with 'user' role or 'admin' role.
    Admins inherit user permissions through role hierarchy.
    """
    authorization = request.headers.get("Authorization")
    
    shared_store = {
        "authorization_header": authorization,
        "required_roles": ["user"]
    }
    
    result = await auth_middleware.run(shared_store)
    
    if not result["authenticated"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"]
        )
    
    return {
        "user_id": result["user_id"],
        "email": result["email"],
        "role": result["role"]
    }


async def require_admin_role(request: Request) -> Dict[str, Any]:
    """
    Dependency requiring admin role only
    
    Restricts access to users with 'admin' role only.
    Regular users will receive 403 Forbidden response.
    """
    authorization = request.headers.get("Authorization")
    
    shared_store = {
        "authorization_header": authorization,
        "required_roles": ["admin"]
    }
    
    result = await auth_middleware.run(shared_store)
    
    if not result["authenticated"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"]
        )
    
    return {
        "user_id": result["user_id"],
        "email": result["email"],
        "role": result["role"]
    }