"""
User Password Node for Theo Authentication System

Cookbook Reference: pocketflow-tool-security

PocketFlow Node implementing secure password hashing and verification
using bcrypt for the authentication system.
Estimated Lines: 35/150
"""

from pocketflow import AsyncNode
from typing import Dict, Any
import bcrypt


class UserPasswordNode(AsyncNode):
    """
    Secure password operations using bcrypt
    
    Cookbook Reference: pocketflow-tool-security
    
    Supports operations: hash_password, verify_password
    Handles secure password hashing with bcrypt salt generation
    """
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method for password operations"""
        try:
            operation = shared_store.get("operation")
            if not operation:
                return {"success": False, "error": "No operation specified"}
            
            if operation == "hash_password":
                return await self._hash_password(shared_store)
            elif operation == "verify_password":
                return await self._verify_password(shared_store)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": f"Password operation failed: {str(e)}"}
    
    async def _hash_password(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Securely hash password using bcrypt"""
        password = shared_store.get("password")
        if not password:
            return {"success": False, "error": "Password required"}
        
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        return {"success": True, "password_hash": password_hash}
    
    async def _verify_password(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Verify password against stored hash"""
        password = shared_store.get("password")
        password_hash = shared_store.get("password_hash")
        
        if not password or not password_hash:
            return {"success": False, "error": "Password and hash required"}
        
        is_valid = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        return {"success": True, "valid": is_valid}