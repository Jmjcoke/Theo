"""
Database Utilities for Theo Application

Provides async SQLite database operations for user authentication
and document management using aiosqlite.
"""

import aiosqlite
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Database path - can be overridden via environment variable
DATABASE_PATH = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")


class DatabaseManager:
    """Async SQLite database manager for Theo application"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
    
    async def init_database(self):
        """Initialize database with schema if it doesn't exist"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Check if users table exists
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
                )
                result = await cursor.fetchone()
                
                if not result:
                    # Read and execute schema file
                    schema_path = "/Users/joshuacoke/dev/Theo/apps/api/database/sqlite_schema.sql"
                    if os.path.exists(schema_path):
                        with open(schema_path, 'r') as f:
                            schema = f.read()
                        await db.executescript(schema)
                        await db.commit()
                        logger.info("Database schema initialized successfully")
                    else:
                        logger.error(f"Schema file not found at {schema_path}")
                        raise FileNotFoundError(f"Schema file not found at {schema_path}")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    async def create_user(self, email: str, password_hash: str, role: str = "user", status: str = "pending") -> Dict[str, Any]:
        """Create new user record"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """INSERT INTO users (email, password_hash, role, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (email, password_hash, role, status, datetime.now(), datetime.now())
                )
                user_id = cursor.lastrowid
                await db.commit()
                
                # Return the created user data
                return {
                    "success": True,
                    "user_id": str(user_id),
                    "user": {
                        "id": user_id,
                        "email": email,
                        "role": role,
                        "status": status,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                }
        except aiosqlite.IntegrityError as e:
            logger.error(f"User creation failed - integrity error: {str(e)}")
            return {"success": False, "error": "User with this email already exists"}
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM users WHERE email = ?",
                    (email,)
                )
                row = await cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Get user by email failed: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM users WHERE id = ?",
                    (user_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Get user by ID failed: {str(e)}")
            return None
    
    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information"""
        try:
            # Build dynamic update query
            update_fields = []
            values = []
            
            for field, value in updates.items():
                if field not in ['id', 'created_at']:  # Don't allow updating these fields
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return {"success": False, "error": "No valid fields to update"}
            
            # Always update the updated_at timestamp
            update_fields.append("updated_at = ?")
            values.append(datetime.now())
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, values)
                await db.commit()
                
                # Return updated user
                updated_user = await self.get_user_by_id(user_id)
                return {
                    "success": True,
                    "user_id": str(user_id),
                    "user": updated_user
                }
                
        except Exception as e:
            logger.error(f"User update failed: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    async def list_users(self, status: Optional[str] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """List users with optional filtering"""
        try:
            query = "SELECT * FROM users"
            params = []
            conditions = []
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if role:
                conditions.append("role = ?")
                params.append(role)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC"
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"List users failed: {str(e)}")
            return []
    
    async def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete user by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                await db.commit()
                
                if cursor.rowcount > 0:
                    return {"success": True, "message": "User deleted successfully"}
                else:
                    return {"success": False, "error": "User not found"}
                    
        except Exception as e:
            logger.error(f"Delete user failed: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}


# Global database manager instance
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        # Use current DATABASE_PATH environment variable
        current_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
        _db_manager = DatabaseManager(current_path)
    return _db_manager


async def init_database():
    """Initialize the database - call this on startup"""
    await get_db_manager().init_database()


# Convenience functions for common operations
async def create_user(email: str, password_hash: str, role: str = "user", status: str = "pending") -> Dict[str, Any]:
    """Create new user"""
    return await get_db_manager().create_user(email, password_hash, role, status)


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    return await get_db_manager().get_user_by_email(email)


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    return await get_db_manager().get_user_by_id(user_id)


async def update_user(user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update user"""
    return await get_db_manager().update_user(user_id, updates)


async def list_users(status: Optional[str] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
    """List users"""
    return await get_db_manager().list_users(status, role)


async def delete_user(user_id: int) -> Dict[str, Any]:
    """Delete user"""
    return await get_db_manager().delete_user(user_id)


async def update_user_status(email: str, status: str) -> bool:
    """Update user status by email"""
    user = await get_user_by_email(email)
    if user:
        result = await update_user(user['id'], {'status': status})
        return result.get('success', False)
    return False


def reset_db_manager():
    """Reset the global database manager - used for testing"""
    global _db_manager
    _db_manager = None