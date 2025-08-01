# Security Architecture

## Input Validation & Sanitization

**Node Input Validation**:
```python
from pydantic import BaseModel, validator

class TheologicalQueryInput(BaseModel):
    query: str
    context: Optional[str] = None
    
    @validator('query')
    def validate_query_length(cls, v):
        if len(v) > 1000:
            raise ValueError('Query too long')
        if len(v.strip()) == 0:
            raise ValueError('Query cannot be empty')
        return v.strip()

class ValidatedInputNode(AsyncNode):
    """Node with automatic input validation"""
    
    input_model = TheologicalQueryInput
    
    async def prep(self, shared_store):
        # Automatic validation using Pydantic
        validated_input = self.input_model(**shared_store["raw_input"])
        return validated_input.dict()
```

## Rate Limiting

**API Rate Limiting**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/chat")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def chat_endpoint(request: Request):
    """Rate-limited chat endpoint"""
    pass
```

This backend architecture provides a robust, scalable foundation for Theo's theological AI assistant, combining FastAPI's performance with PocketFlow's workflow orchestration capabilities while maintaining security, observability, and maintainability standards.