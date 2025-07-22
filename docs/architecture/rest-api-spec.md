# REST API Specification

## Overview

This document defines the comprehensive REST API specification for Theo's theological AI assistant backend, including authentication patterns, request/response formats, error handling, and API design standards.

## API Design Principles

### 1. RESTful Design Standards
- **Resource-Based URLs**: Use nouns, not verbs (`/api/documents`, not `/api/get-documents`)
- **HTTP Methods**: GET (read), POST (create), PUT (update/replace), PATCH (partial update), DELETE (remove)
- **Status Codes**: Meaningful HTTP status codes for all responses
- **Stateless**: Each request contains all necessary information

### 2. Naming Conventions
- **Endpoints**: kebab-case (`/api/user-management`, `/api/document-upload`)
- **JSON Keys**: camelCase (`userId`, `createdAt`, `processingStatus`)  
- **Query Parameters**: camelCase (`userId=123`, `sortBy=createdAt`)
- **Headers**: Pascal-Case (`Content-Type`, `Authorization`, `X-Request-ID`)

### 3. Versioning Strategy
- **URL Versioning**: `/api/v1/`, `/api/v2/` for major changes
- **Header Versioning**: `Accept: application/vnd.theo.v1+json` for specific clients
- **Backward Compatibility**: Maintain previous versions for 6 months minimum

## Base API Configuration

### Base URL Structure
```
Development: http://localhost:8000/api
Production:  https://api.theo-ai.com/api
```

### Standard Headers

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

## Authentication & Authorization

### Authentication Endpoints

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

### Authorization Header Format
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Protected Route Pattern
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

## Core API Endpoints

### System Health

**GET /health**
```http
GET /health
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok",
  "timestamp": "2025-07-22T10:30:00Z",
  "version": "1.0.0",
  "environment": "development"
}
```

**Extended Health Check** (for monitoring):
```http
GET /health/detailed
Authorization: Bearer <admin_token>
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok",
  "timestamp": "2025-07-22T10:30:00Z",
  "services": {
    "database": "ok",
    "redis": "ok", 
    "openai": "ok",
    "supabase": "ok"
  },
  "metrics": {
    "uptime": 86400,
    "requestCount": 1542,
    "averageResponseTime": 120
  }
}
```

### Document Management

**POST /api/documents/upload**
```http
POST /api/documents/upload
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data

file: <document_file>
documentType: biblical|theological
category: <optional_category>
```

**Response**:
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "documentId": "doc-uuid-123",
  "filename": "genesis-commentary.pdf",
  "documentType": "theological",
  "processingStatus": "queued",
  "uploadedAt": "2025-07-22T10:30:00Z",
  "jobId": "job-uuid-456"
}
```

**GET /api/documents**
```http
GET /api/documents?page=1&limit=20&status=completed&type=biblical
Authorization: Bearer <token>
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "documents": [
    {
      "id": "doc-uuid-123",
      "filename": "genesis-commentary.pdf",
      "documentType": "theological", 
      "processingStatus": "completed",
      "uploadedAt": "2025-07-22T10:30:00Z",
      "processedAt": "2025-07-22T10:32:15Z",
      "chunkCount": 156,
      "metadata": {
        "author": "John Calvin",
        "language": "en",
        "wordCount": 45123
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

**DELETE /api/documents/{documentId}**
```http
DELETE /api/documents/doc-uuid-123
Authorization: Bearer <admin_token>
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Document deleted successfully",
  "documentId": "doc-uuid-123",
  "deletedAt": "2025-07-22T10:35:00Z"
}
```

### Chat & Query System

**POST /api/chat**
```http
POST /api/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What does Genesis 1:1 teach us about creation?",
  "context": "biblical-exegesis",
  "sessionId": "session-uuid-789"
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "response": "Genesis 1:1 establishes the foundational truth that God is the creator of all things...",
  "confidence": 0.92,
  "sources": [
    {
      "documentId": "doc-uuid-123",
      "title": "Genesis Commentary",
      "excerpt": "In the beginning God created the heavens and the earth...",
      "relevance": 0.95,
      "citation": "Genesis 1:1 (ESV)"
    }
  ],
  "processingTime": 1250,
  "sessionId": "session-uuid-789",
  "messageId": "msg-uuid-101"
}
```

**GET /api/chat/history/{sessionId}**
```http
GET /api/chat/history/session-uuid-789?limit=50
Authorization: Bearer <token>
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "sessionId": "session-uuid-789",
  "messages": [
    {
      "id": "msg-uuid-101",
      "type": "user",
      "content": "What does Genesis 1:1 teach us about creation?",
      "timestamp": "2025-07-22T10:30:00Z"
    },
    {
      "id": "msg-uuid-102", 
      "type": "assistant",
      "content": "Genesis 1:1 establishes the foundational truth...",
      "confidence": 0.92,
      "sources": [...],
      "timestamp": "2025-07-22T10:30:01Z"
    }
  ],
  "totalMessages": 24
}
```

### Background Job Status

**GET /api/jobs/{jobId}/status**
```http
GET /api/jobs/job-uuid-456/status
Authorization: Bearer <token>
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "jobId": "job-uuid-456",
  "status": "processing",
  "progress": 0.65,
  "currentStep": "generating-embeddings", 
  "estimatedTimeRemaining": 120,
  "startedAt": "2025-07-22T10:30:00Z",
  "updatedAt": "2025-07-22T10:32:00Z"
}
```

### Server-Sent Events for Real-time Updates

**GET /api/jobs/{jobId}/events**
```http
GET /api/jobs/job-uuid-456/events
Authorization: Bearer <token>
Accept: text/event-stream
```

**Response Stream**:
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"status": "processing", "progress": 0.25, "step": "parsing-document"}

data: {"status": "processing", "progress": 0.50, "step": "generating-chunks"}

data: {"status": "processing", "progress": 0.75, "step": "generating-embeddings"}

data: {"status": "completed", "progress": 1.0, "step": "storing-vectors"}
```

### Admin Endpoints

**GET /api/admin/users**
```http
GET /api/admin/users?status=pending&page=1&limit=20
Authorization: Bearer <admin_token>
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "users": [
    {
      "id": "user-uuid-123",
      "email": "user@example.com",
      "role": "user",
      "status": "pending",
      "registeredAt": "2025-07-22T09:15:00Z",
      "lastLoginAt": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "pages": 1
  }
}
```

**PATCH /api/admin/users/{userId}**
```http
PATCH /api/admin/users/user-uuid-123
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "status": "approved"
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "User status updated successfully",
  "user": {
    "id": "user-uuid-123",
    "email": "user@example.com",
    "status": "approved",
    "updatedAt": "2025-07-22T10:40:00Z"
  }
}
```

## Error Response Format

### Standard Error Structure
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

### Common Error Responses

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

## Query Parameters & Filtering

### Standard Query Parameters

**Pagination**:
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 20, max: 100) - Items per page

**Sorting**:  
- `sortBy` (string) - Field to sort by
- `sortOrder` (string: "asc"|"desc", default: "desc") - Sort direction

**Filtering**:
- `status` (string) - Filter by status
- `type` (string) - Filter by type/category  
- `search` (string) - Text search across relevant fields
- `dateFrom` (ISO date) - Filter from date
- `dateTo` (ISO date) - Filter to date

### Example Query String
```http
GET /api/documents?page=2&limit=50&sortBy=createdAt&sortOrder=desc&status=completed&search=genesis&dateFrom=2025-01-01T00:00:00Z
```

## Request/Response Size Limits

### Size Constraints
- **Request Body**: Maximum 10MB for file uploads, 1MB for JSON
- **Response Body**: Maximum 5MB, paginate large datasets
- **Query String**: Maximum 2KB
- **Headers**: Maximum 8KB total

### File Upload Limits
- **Document Upload**: Maximum 50MB per file
- **Supported Formats**: PDF, DOCX, TXT, MD
- **Batch Upload**: Maximum 10 files per request

## Rate Limiting

### Rate Limit Tiers

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

### Rate Limit Headers
```http
X-Rate-Limit-Limit: 30
X-Rate-Limit-Remaining: 25
X-Rate-Limit-Reset: 1642781400
X-Rate-Limit-Window: 60
```

## Content Types & Formats

### Supported Content Types

**Request Content Types**:
- `application/json` - All JSON endpoints
- `multipart/form-data` - File uploads
- `text/plain` - Simple text endpoints

**Response Content Types**:
- `application/json` - Standard API responses
- `text/event-stream` - Server-Sent Events
- `application/octet-stream` - File downloads

### Date/Time Format
- **ISO 8601**: `2025-07-22T10:30:00Z` (UTC timezone)
- **Unix Timestamp**: Accepted in requests, not used in responses

### UUID Format
- **Version 4 UUIDs**: `123e4567-e89b-12d3-a456-426614174000`
- Used for all entity IDs (users, documents, sessions, etc.)

## WebSocket Endpoints

### Real-time Chat

**WebSocket Connection**:
```
ws://localhost:8000/api/ws/chat?token=<jwt_token>&sessionId=<session_uuid>
```

**Message Format** (Client → Server):
```json
{
  "type": "message",
  "content": "What does Romans 3:23 mean?",
  "context": "biblical-exegesis",
  "messageId": "msg-uuid-client-123"
}
```

**Response Format** (Server → Client):
```json
{
  "type": "response",
  "messageId": "msg-uuid-server-456",
  "replyTo": "msg-uuid-client-123",
  "content": "Romans 3:23 teaches us about universal sinfulness...",
  "confidence": 0.94,
  "sources": [...],
  "timestamp": "2025-07-22T10:30:00Z"
}
```

**Connection Events**:
```json
{"type": "connected", "sessionId": "session-uuid-789"}
{"type": "typing", "isTyping": true}
{"type": "processing", "status": "analyzing_query"}
{"type": "error", "error": "processing_failed", "message": "..."}
```

## API Testing & Development

### Health Check Testing
```bash
# Basic health check
curl -X GET http://localhost:8000/health

# Expected response
# {"status": "ok", "timestamp": "2025-07-22T10:30:00Z"}
```

### Authentication Testing
```bash
# Register new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# Login user  
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'
```

### Protected Endpoint Testing
```bash
# Use JWT token from login response
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Test protected endpoint
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer $TOKEN"
```

This comprehensive REST API specification provides the foundation for building and integrating with Theo's theological AI assistant backend, ensuring consistent, secure, and well-documented API interactions.