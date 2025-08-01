# WebSocket Endpoints

## Real-time Chat

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
