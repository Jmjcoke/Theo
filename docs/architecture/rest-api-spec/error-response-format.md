# Error Response Format

## Standard Error Structure
```http
HTTP/1.1 <status_code> <status_text>
Content-Type: application/json

{
  "error": "<error_code>",
  "message": "<human_readable_message>", 
  "details": "<specific_error_details>",
  "timestamp": "2025-07-22T10:30:00Z",
  "requestId": "<request_uuid>",
  "path": "/api/endpoint",
  "suggestions": ["<actionable_suggestion>"]
}
```

## Common Error Responses

**400 Bad Request**:
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  },
  "timestamp": "2025-07-22T10:30:00Z",
  "requestId": "req-uuid-123"
}
```

**401 Unauthorized**:
```json
{
  "error": "authentication_required",
  "message": "Valid authentication token required",
  "suggestions": ["Include 'Authorization: Bearer <token>' header"],
  "timestamp": "2025-07-22T10:30:00Z"
}
```

**403 Forbidden**:
```json
{
  "error": "insufficient_permissions", 
  "message": "Admin role required for this operation",
  "details": "User role 'user' cannot access admin endpoints",
  "timestamp": "2025-07-22T10:30:00Z"
}
```

**404 Not Found**:
```json
{
  "error": "resource_not_found",
  "message": "Document not found",
  "details": "Document with ID 'doc-uuid-123' does not exist",
  "timestamp": "2025-07-22T10:30:00Z"
}
```

**422 Unprocessable Entity**:
```json
{
  "error": "validation_error",
  "message": "Input validation failed",
  "details": [
    {
      "field": "password",
      "error": "Password must be at least 8 characters long"
    },
    {
      "field": "email", 
      "error": "Email address is required"
    }
  ],
  "timestamp": "2025-07-22T10:30:00Z"
}
```

**429 Too Many Requests**:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "details": "Rate limit: 10 requests per minute",
  "retryAfter": 45,
  "timestamp": "2025-07-22T10:30:00Z"
}
```

**500 Internal Server Error**:
```json
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred",
  "requestId": "req-uuid-123",
  "timestamp": "2025-07-22T10:30:00Z",
  "suggestions": ["Try again later", "Contact support if issue persists"]
}
```
