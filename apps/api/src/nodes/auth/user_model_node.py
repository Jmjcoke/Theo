"""
User Data Node for Theo Authentication System

Cookbook Reference: pocketflow-tool-database

PocketFlow Node implementing user CRUD operations for authentication system.
Works with UserValidationNode and UserPasswordNode for complete user management.
Now integrated with SQLite database for persistent storage.
Estimated Lines: 75/150
"""

from pocketflow import AsyncNode
from typing import Dict, Any
from datetime import datetime
import uuid
from src.utils.database_utils import (
    create_user as db_create_user,
    get_user_by_email as db_get_user_by_email,
    get_user_by_id as db_get_user_by_id,
    update_user as db_update_user
)


class UserDataNode(AsyncNode):
    """
    User CRUD operations for database management
    
    Cookbook Reference: pocketflow-tool-database
    
    Supports operations: create_user, get_user, update_user
    Works in conjunction with UserValidationNode and UserPasswordNode
    """
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method for user data operations"""
        try:
            operation = shared_store.get("operation")
            if not operation:
                return {"success": False, "error": "No operation specified"}
            
            if operation == "create_user":
                return await self._create_user(shared_store)
            elif operation == "get_user":
                return await self._get_user(shared_store)
            elif operation == "update_user":
                return await self._update_user(shared_store)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": f"Operation failed: {str(e)}"}
    
    async def _create_user(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user record in SQLite database"""
        email = shared_store.get("email")
        password_hash = shared_store.get("password_hash")
        role = shared_store.get("role", "user")
        status = shared_store.get("status", "pending")
        
        if not email or not password_hash:
            return {"success": False, "error": "Email and password_hash required"}
        
        # Use database utility to create user
        result = await db_create_user(email, password_hash, role, status)
        return result
    
    async def _get_user(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Get user by email or ID from SQLite database"""
        email = shared_store.get("email")
        user_id = shared_store.get("user_id")
        
        if not email and not user_id:
            return {"success": False, "error": "Email or user_id required"}
        
        try:
            user = None
            if email:
                user = await db_get_user_by_email(email)
            elif user_id:
                user = await db_get_user_by_id(int(user_id))
            
            return {
                "success": True,
                "user": user
            }
        except Exception as e:
            return {"success": False, "error": f"Database query failed: {str(e)}"}
    
    async def _update_user(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information in SQLite database"""
        user_id = shared_store.get("user_id")
        updates = shared_store.get("updates", {})
        
        if not user_id:
            return {"success": False, "error": "User ID required"}
        
        # Use database utility to update user
        result = await db_update_user(int(user_id), updates)
        return result