"""
User Registration Node for Theo Authentication System

Cookbook Reference: pocketflow-fastapi-background

PocketFlow Node implementing user registration endpoint with security validation,
password policy enforcement, and duplicate user checking.
Estimated Lines: 145/150
"""

from pocketflow import AsyncNode
from typing import Dict, Any
from pydantic import BaseModel, EmailStr, field_validator
import re
from .user_validation_node import UserValidationNode
from .user_password_node import UserPasswordNode
from .user_model_node import UserDataNode


class RegistrationRequest(BaseModel):
    """User registration request validation with security policies"""
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password meets security policy"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')  
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserRegistrationNode(AsyncNode):
    """
    User registration endpoint with security validation
    
    Cookbook Reference: pocketflow-fastapi-background
    
    Handles user registration with password policy validation,
    email uniqueness checking, and secure account creation
    """
    
    def __init__(self):
        super().__init__()
        self.validation_node = UserValidationNode()
        self.password_node = UserPasswordNode()
        self.data_node = UserDataNode()
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Main registration endpoint logic"""
        try:
            # Extract registration data
            registration_data = shared_store.get("registration_data")
            if not registration_data:
                return self._error_response("Missing registration data", 400)
            
            # Validate input with Pydantic
            try:
                request = RegistrationRequest(**registration_data)
            except Exception as e:
                return self._error_response(f"Validation error: {str(e)}", 400)
            
            # Check if user already exists
            if await self._check_user_exists(request.email):
                return self._error_response("User with this email already exists", 409)
            
            # Hash password
            password_result = await self.password_node.run({
                "operation": "hash_password",
                "password": request.password
            })
            
            if not password_result["success"]:
                return self._error_response("Password processing failed", 500)
            
            # Create user data
            user_data = {
                "email": request.email,
                "password_hash": password_result["password_hash"],
                "role": "user",
                "status": "pending"
            }
            
            # Validate user data
            validation_result = await self.validation_node.run({
                "user_data": user_data
            })
            
            if not validation_result["success"]:
                return self._error_response("User data validation failed", 500)
            
            # Create user record
            creation_result = await self.data_node.run({
                "operation": "create_user",
                **user_data
            })
            
            if creation_result["success"]:
                return {
                    "success": True,
                    "message": "Registration successful. Account is pending admin approval.",
                    "user_id": creation_result["user_id"],
                    "status_code": 201
                }
            else:
                return self._error_response(creation_result["error"], 500)
                
        except Exception as e:
            return self._error_response(f"Registration failed: {str(e)}", 500)
    
    async def _check_user_exists(self, email: str) -> bool:
        """Check if user already exists"""
        result = await self.data_node.run({
            "operation": "get_user",
            "email": email
        })
        return result.get("user") is not None
    
    def _error_response(self, error_message: str, status_code: int) -> Dict[str, Any]:
        """Standard error response format"""
        return {
            "success": False,
            "error": error_message,
            "status_code": status_code
        }