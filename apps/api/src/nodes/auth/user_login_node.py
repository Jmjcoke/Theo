"""
User Login Node for Theo Authentication System

Cookbook Reference: pocketflow-fastapi-background

PocketFlow Node implementing secure user login with JWT token generation,
password verification, and user status validation.
Estimated Lines: 140/150
"""

from pocketflow import AsyncNode
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timedelta
import bcrypt
import os
from .user_validation_node import UserValidationNode
from .user_password_node import UserPasswordNode
from .user_model_node import UserDataNode


class LoginRequest(BaseModel):
    """User login request validation"""
    email: EmailStr
    password: str


class UserLoginNode(AsyncNode):
    """
    User login with JWT token generation and validation
    
    Cookbook Reference: pocketflow-fastapi-background
    
    Handles secure user authentication with password verification,
    status checking, and JWT token generation for approved users
    """
    
    def __init__(self):
        super().__init__()
        self.password_node = UserPasswordNode()
        self.data_node = UserDataNode()
        # Use environment variable for production security
        self.secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
        self.algorithm = "HS256"
        self.token_expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Main login endpoint logic"""
        try:
            # Extract login data
            login_data = shared_store.get("login_data")
            if not login_data:
                return self._error_response("Missing login data", 400)
            
            # Validate input
            try:
                request = LoginRequest(**login_data)
            except Exception as e:
                return self._error_response(f"Invalid input: {str(e)}", 400)
            
            # Get user from database
            user = await self._get_user_by_email(request.email)
            if not user:
                return self._error_response("Invalid credentials", 401)
            
            # Check user status
            if user.get("status") != "approved":
                return self._error_response(
                    "Account not approved. Please contact administrator.", 403
                )
            
            # Verify password
            password_valid = await self._verify_password(request.password, user["password_hash"])
            if not password_valid:
                return self._error_response("Invalid credentials", 401)
            
            # Generate JWT token
            token = await self._generate_jwt_token(user)
            
            return {
                "success": True,
                "access_token": token,
                "token_type": "bearer",
                "user_id": str(user["id"]),
                "user_role": user["role"],
                "status_code": 200
            }
            
        except Exception as e:
            return self._error_response(f"Login failed: {str(e)}", 500)
    
    async def _get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email using UserDataNode"""
        result = await self.data_node.run({
            "operation": "get_user",
            "email": email
        })
        return result.get("user")
    
    async def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password using UserPasswordNode"""
        result = await self.password_node.run({
            "operation": "verify_password",
            "password": password,
            "password_hash": password_hash
        })
        return result.get("valid", False)
    
    async def _generate_jwt_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT access token"""
        from datetime import timezone
        
        now = datetime.now(timezone.utc)
        expiration = now + timedelta(hours=self.token_expire_hours)
        
        payload = {
            "user_id": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
            "exp": expiration,
            "iat": now
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def _error_response(self, error_message: str, status_code: int) -> Dict[str, Any]:
        """Standard error response format"""
        return {
            "success": False,
            "error": error_message,
            "status_code": status_code
        }