"""
Protected API Routes for Theo

FastAPI router with protected endpoints demonstrating role-based access control.
Includes test endpoints for user and admin access levels.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from src.middleware.auth_dependencies import get_current_user, require_user_role, require_admin_role

router = APIRouter()


@router.get("/protected/user-test")
async def user_test_endpoint(current_user: Dict[str, Any] = Depends(require_user_role)):
    """
    Test endpoint accessible to users and admins
    
    Demonstrates user-level protection where both 'user' and 'admin' 
    roles can access the endpoint through role hierarchy.
    """
    return {
        "message": "Access granted to protected user endpoint",
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"]
    }


@router.get("/protected/admin-test")
async def admin_test_endpoint(current_user: Dict[str, Any] = Depends(require_admin_role)):
    """
    Test endpoint accessible to admins only
    
    Demonstrates admin-only protection where only 'admin' role 
    users can access the endpoint. Regular users receive 403 Forbidden.
    """
    return {
        "message": "Access granted to protected admin endpoint",
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"]
    }


@router.get("/protected/profile")
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user profile
    
    Accessible to any authenticated user regardless of role.
    Returns user information from the JWT token.
    """
    return {
        "profile": {
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "role": current_user["role"]
        },
        "message": "Profile retrieved successfully"
    }


@router.get("/protected/health")
async def protected_health_check(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Protected health check endpoint
    
    Basic authenticated endpoint for testing token validation.
    Accessible to any authenticated user.
    """
    return {
        "status": "healthy",
        "service": "protected-api",
        "authenticated_user": current_user["user_id"]
    }


from pydantic import BaseModel
import bcrypt
import aiosqlite
from src.core.config import settings

class ProfileUpdateRequest(BaseModel):
    """Request model for profile updates"""
    email: str = None
    current_password: str = None
    new_password: str = None

class PasswordChangeRequest(BaseModel):
    """Request model for password changes"""
    current_password: str
    new_password: str


@router.patch("/protected/profile")
async def update_profile(
    profile_update: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update user profile (email and/or password)
    
    Users can update their email and password. Password change requires 
    current password verification for security.
    """
    try:
        async with aiosqlite.connect("theo.db") as conn:
            # If changing password, verify current password first
            if profile_update.new_password:
                if not profile_update.current_password:
                    raise HTTPException(
                        status_code=400,
                        detail="Current password required to change password"
                    )
                
                # Get current password hash
                cursor = await conn.execute(
                    "SELECT password_hash FROM users WHERE id = ?",
                    (current_user["user_id"],)
                )
                row = await cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Verify current password
                if not bcrypt.checkpw(
                    profile_update.current_password.encode('utf-8'),
                    row[0].encode('utf-8')
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Current password is incorrect"
                    )
                
                # Hash new password
                salt = bcrypt.gensalt()
                new_password_hash = bcrypt.hashpw(
                    profile_update.new_password.encode('utf-8'), 
                    salt
                ).decode('utf-8')
                
                # Update password
                await conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (new_password_hash, current_user["user_id"])
                )
            
            # Update email if provided
            if profile_update.email:
                # Check if email already exists
                cursor = await conn.execute(
                    "SELECT id FROM users WHERE email = ? AND id != ?",
                    (profile_update.email, current_user["user_id"])
                )
                existing = await cursor.fetchone()
                
                if existing:
                    raise HTTPException(
                        status_code=400,
                        detail="Email already in use"
                    )
                
                # Update email
                await conn.execute(
                    "UPDATE users SET email = ? WHERE id = ?",
                    (profile_update.email, current_user["user_id"])
                )
            
            await conn.commit()
            
            # Get updated user info
            cursor = await conn.execute(
                "SELECT id, email, role, status FROM users WHERE id = ?",
                (current_user["user_id"],)
            )
            updated_user = await cursor.fetchone()
            
            return {
                "message": "Profile updated successfully",
                "profile": {
                    "user_id": str(updated_user[0]),
                    "email": updated_user[1],
                    "role": updated_user[2],
                    "status": updated_user[3]
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update profile: {str(e)}"
        )