# Authentication & Authorization

## Authentication Endpoints

**POST /api/auth/register**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response**:
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "message": "Registration successful",
  "userId": "user-uuid-123",
  "status": "pending",
  "nextStep": "Account pending admin approval"
}
```

**POST /api/auth/login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com", 
  "password": "SecurePassword123!"
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "user": {
    "id": "user-uuid-123",
    "email": "user@example.com",
    "role": "user",
    "status": "approved"
  }
}
```

## Authorization Header Format
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Protected Route Pattern
All protected endpoints return `401 Unauthorized` if token is missing/invalid:
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": "authentication_required",
  "message": "Valid authentication token required",
  "timestamp": "2025-07-22T10:30:00Z"
}
```
