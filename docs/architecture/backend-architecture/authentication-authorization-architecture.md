# Authentication & Authorization Architecture

## JWT-Based Authentication Pattern

**Authentication Flow**:
```python
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

class AuthenticationNode(AsyncNode):
    """Handles user authentication via JWT"""
    
    async def exec(self, credentials):
        # Validate credentials against database
        user = await self.validate_user(credentials)
        
        # Generate JWT token
        token = self.create_jwt_token(user)
        
        return {"token": token, "user": user}

def verify_token(token: str = Depends(security)):
    """Dependency for protected routes"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Role-Based Authorization

**Authorization Patterns**:
```python
def require_role(required_role: str):
    """Decorator for role-based access control"""
    def role_checker(current_user = Depends(verify_token)):
        if current_user.get("role") != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
