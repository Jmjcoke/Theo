"""
JWT Validation Node for Theo Authentication System

Cookbook Reference: pocketflow-tool-security

PocketFlow Node implementing JWT token validation for protected routes
with secure token decoding and payload extraction.
Estimated Lines: 60/150
"""

from pocketflow import AsyncNode
from typing import Dict, Any
import jwt
import os


class JWTValidationNode(AsyncNode):
    """
    JWT token validation for protected routes
    
    Cookbook Reference: pocketflow-tool-security
    
    Validates JWT tokens, extracts user information, and handles
    token expiration and invalid token scenarios
    """
    
    def __init__(self):
        super().__init__()
        self.secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
        self.algorithm = "HS256"
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JWT token and extract user information"""
        try:
            token = shared_store.get("token")
            if not token:
                return {"valid": False, "error": "No token provided"}
            
            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token[7:]
            
            # Decode and validate token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            return {
                "valid": True,
                "user_id": payload["user_id"],
                "email": payload["email"],
                "role": payload["role"],
                "exp": payload["exp"],
                "iat": payload["iat"]
            }
            
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
        except Exception as e:
            return {"valid": False, "error": f"Token validation failed: {str(e)}"}