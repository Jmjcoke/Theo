"""
Authentication API Routes for Theo

FastAPI router for authentication endpoints including user registration,
login, and account management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, ValidationError
from src.nodes.auth.user_registration_node import UserRegistrationNode, RegistrationRequest
from src.nodes.auth.user_login_node import UserLoginNode, LoginRequest

router = APIRouter()
registration_node = UserRegistrationNode()
login_node = UserLoginNode()


class RegistrationResponse(BaseModel):
    """Response model for successful registration"""
    message: str
    user_id: str


class LoginResponse(BaseModel):
    """Response model for successful login"""
    access_token: str
    token_type: str
    user_id: str
    user_role: str


@router.post("/register", response_model=RegistrationResponse, status_code=201)
async def register_user(validated_request: RegistrationRequest):
    """
    Public endpoint for user registration
    
    Creates a new user account with 'pending' status for admin review.
    Password must meet security policy requirements.
    """
    
    shared_store = {
        "registration_data": validated_request.model_dump()
    }
    
    result = await registration_node.run(shared_store)
    
    if result["success"]:
        return RegistrationResponse(
            message=result["message"],
            user_id=result["user_id"]
        )
    else:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"]
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(validated_request: LoginRequest):
    """
    Public endpoint for user login
    
    Authenticates user credentials and returns JWT access token
    for approved users only.
    """
    
    shared_store = {
        "login_data": validated_request.model_dump()
    }
    
    result = await login_node.run(shared_store)
    
    if result["success"]:
        return LoginResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            user_id=result["user_id"],
            user_role=result["user_role"]
        )
    else:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"]
        )


@router.get("/health")
async def auth_health_check():
    """Health check endpoint for authentication service"""
    return {"status": "healthy", "service": "authentication"}