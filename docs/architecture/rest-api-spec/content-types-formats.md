# Content Types & Formats

## Supported Content Types

**Request Content Types**:
- `application/json` - All JSON endpoints
- `multipart/form-data` - File uploads
- `text/plain` - Simple text endpoints

**Response Content Types**:
- `application/json` - Standard API responses
- `text/event-stream` - Server-Sent Events
- `application/octet-stream` - File downloads

## Date/Time Format
- **ISO 8601**: `2025-07-22T10:30:00Z` (UTC timezone)
- **Unix Timestamp**: Accepted in requests, not used in responses

## UUID Format
- **Version 4 UUIDs**: `123e4567-e89b-12d3-a456-426614174000`
- Used for all entity IDs (users, documents, sessions, etc.)
