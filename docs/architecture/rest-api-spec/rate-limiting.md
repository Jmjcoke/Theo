# Rate Limiting

## Rate Limit Tiers

**Authentication Endpoints**:
- Login: 5 attempts per minute per IP
- Register: 3 attempts per minute per IP

**Chat Endpoints**: 
- Authenticated users: 30 requests per minute
- Premium users: 100 requests per minute

**Admin Endpoints**:
- 60 requests per minute

**File Upload**:
- 10 uploads per hour per user

## Rate Limit Headers
```http
X-Rate-Limit-Limit: 30
X-Rate-Limit-Remaining: 25
X-Rate-Limit-Reset: 1642781400
X-Rate-Limit-Window: 60
```
