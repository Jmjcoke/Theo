# Base API Configuration

## Base URL Structure
```
Development: http://localhost:8000/api
Production:  https://api.theo-ai.com/api
```

## Standard Headers

**Request Headers**:
```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <jwt_token>  # For protected endpoints
X-Request-ID: <uuid>              # For request tracking
User-Agent: <client_info>         # Client identification
```

**Response Headers**:
```http
Content-Type: application/json
X-Request-ID: <uuid>              # Echo request ID
X-Response-Time: <milliseconds>   # Processing time
X-Rate-Limit-Remaining: <count>   # Rate limit status
```
