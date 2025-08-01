# Core API Endpoints

## System Health

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

## Document Management

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

## Chat & Query System

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

## Background Job Status

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

## Server-Sent Events for Real-time Updates

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

## Admin Endpoints

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
