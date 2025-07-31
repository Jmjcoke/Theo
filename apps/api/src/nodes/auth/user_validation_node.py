"""
User Validation Node for Theo Authentication System

Cookbook Reference: pocketflow-tool-validation

PocketFlow Node implementing Pydantic user data validation models
and field validation for the authentication system.
Estimated Lines: 40/150
"""

from pocketflow import AsyncNode
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class UserModel(BaseModel):
    """Pydantic model for user data validation"""
    id: Optional[str] = None
    email: EmailStr
    password_hash: str
    role: str = "user"
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['user', 'admin']:
            raise ValueError('Role must be either "user" or "admin"')
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['pending', 'approved', 'denied']:
            raise ValueError('Status must be "pending", "approved", or "denied"')
        return v


class UserValidationNode(AsyncNode):
    """
    User data validation using Pydantic models
    
    Cookbook Reference: pocketflow-tool-validation
    
    Validates user data structure, email format, roles, and status values
    """
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user data using Pydantic model"""
        try:
            user_data = shared_store.get("user_data", {})
            if not user_data:
                return {"success": False, "error": "No user data to validate"}
            
            # Validate with Pydantic
            user_model = UserModel(**user_data)
            
            return {
                "success": True,
                "validated_data": user_model.model_dump(),
                "valid": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Validation failed: {str(e)}",
                "valid": False
            }