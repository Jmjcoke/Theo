"""
User Password Node for Theo Authentication System

Cookbook Reference: pocketflow-tool-security

PocketFlow Node implementing secure password hashing and verification
using bcrypt for the authentication system with async thread pool execution
to prevent event loop blocking.
Estimated Lines: 35/150
"""

from pocketflow import AsyncNode
from typing import Dict, Any
import bcrypt
import asyncio
import concurrent.futures


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
        """Securely hash password using bcrypt with thread pool to prevent blocking"""
        password = shared_store.get("password")
        if not password:
            return {"success": False, "error": "Password required"}
        
        try:
            # Use thread pool to prevent bcrypt from blocking the event loop
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                password_hash = await loop.run_in_executor(
                    executor,
                    self._sync_hash_password,
                    password
                )
            
            return {"success": True, "password_hash": password_hash}
        except Exception as e:
            return {"success": False, "error": f"Password hashing failed: {str(e)}"}
    
    async def _verify_password(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Verify password against stored hash with thread pool to prevent blocking"""
        password = shared_store.get("password")
        password_hash = shared_store.get("password_hash")
        
        if not password or not password_hash:
            return {"success": False, "error": "Password and hash required"}
        
        try:
            # Use thread pool to prevent bcrypt from blocking the event loop
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                is_valid = await loop.run_in_executor(
                    executor,
                    self._sync_verify_password,
                    password,
                    password_hash
                )
            
            return {"success": True, "valid": is_valid}
        except Exception as e:
            return {"success": False, "error": f"Password verification failed: {str(e)}"}
    
    def _sync_hash_password(self, password: str) -> str:
        """Synchronous bcrypt hashing for thread pool execution"""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        return password_hash
    
    def _sync_verify_password(self, password: str, password_hash: str) -> bool:
        """Synchronous bcrypt verification for thread pool execution"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))