# Backend Architecture

## Overview

Theo's backend is built on FastAPI with PocketFlow workflow orchestration, designed for theological AI assistance with comprehensive document processing, real-time chat, and background job processing capabilities.

## Core Architecture Principles

### 1. PocketFlow-First Design
- **Node/Flow Pattern**: All AI workflows implemented as PocketFlow Nodes (≤150 lines) orchestrated by Flows
- **Async Processing**: AsyncNodes for I/O operations, AsyncFlows for complex orchestration
- **Shared Store Communication**: Nodes communicate exclusively via shared store patterns
- **Cookbook Compliance**: All implementations follow proven PocketFlow cookbook patterns

### 2. Modular Application Structure
```
apps/api/src/
├── nodes/           # PocketFlow Node implementations (≤150 lines each)
│   ├── auth/        # Authentication processing
│   ├── chat/        # Real-time chat processing  
│   ├── documents/   # Document analysis
│   └── workflows/   # Workflow orchestration
├── flows/           # PocketFlow Flow compositions
├── api/             # FastAPI route definitions
├── core/            # Core application logic
├── utils/           # Utility functions
└── admin/           # Admin interface logic
```

### 3. Scalable Processing Architecture
- **Real-time Processing**: FastAPI endpoints trigger PocketFlow Flows for immediate responses
- **Background Processing**: Celery/Redis queue for long-running document processing workflows
- **Event-driven Updates**: Server-Sent Events (SSE) for real-time progress updates

## Application Layer Architecture

### FastAPI Application Structure

**Core Application (`main.py`)**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pocketflow import FlowManager

app = FastAPI(title="Theo Theological AI Assistant")

# CORS middleware for frontend integration
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# PocketFlow integration
flow_manager = FlowManager()

# Route organization
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api/chat") 
app.include_router(documents_router, prefix="/api/documents")
app.include_router(admin_router, prefix="/api/admin")
```

**Health Monitoring Pattern**:
```python
@app.get("/health")
async def health_check():
    """
    System health check endpoint
    Returns: {"status": "ok"} for healthy system
    """
    # Basic health validation
    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version
    }
    
    # Optional: PocketFlow health check
    if flow_manager:
        health_status["pocketflow"] = "ready"
    
    return health_status
```

### Request/Response Flow Architecture

**Standard Request Pattern**:
```
Frontend Request → FastAPI Route → PocketFlow Flow → Nodes → Response
```

**Background Processing Pattern**:
```
Frontend Request → FastAPI Route → Celery Task → AsyncFlow → AsyncNodes → SSE Updates
```

**Real-time Communication Pattern**:
```
WebSocket Connection → FastAPI WebSocket → Chat Flow → Response Stream
```

## PocketFlow Integration Architecture

### Node Architecture Patterns

**Standard Node Structure**:
```python
from pocketflow import Node, AsyncNode

class TheologicalAnalysisNode(AsyncNode):
    """
    Analyzes theological content using biblical hermeneutics
    Max 150 lines including imports and docstrings
    """
    
    async def prep(self, shared_store):
        """Validate inputs and prepare execution"""
        required_keys = ["theological_query", "context"]
        self.validate_shared_store(shared_store, required_keys)
        return shared_store["theological_query"]
    
    async def exec(self, data):
        """Core theological analysis logic"""
        # Implementation limited to ~100 lines
        analysis = await self.perform_analysis(data)
        return analysis
    
    async def post(self, result, shared_store):
        """Update shared store with results"""
        shared_store["theological_analysis"] = result
        shared_store["analysis_confidence"] = result.get("confidence", 0.0)
```

**AsyncNode for I/O Operations**:
```python
class DatabaseQueryNode(AsyncNode):
    """All database operations use AsyncNode pattern"""
    
    async def exec(self, data):
        # Database connections
        async with self.db.get_connection() as conn:
            result = await conn.fetch(data["query"])
        return result
```

### Flow Orchestration Architecture

**Sequential Flow Pattern**:
```python
class TheologicalWorkflow(AsyncFlow):
    """Orchestrates theological analysis workflow"""
    
    def __init__(self):
        self.validation_node = InputValidationNode()
        self.analysis_node = TheologicalAnalysisNode()
        self.citation_node = CitationGenerationNode()
    
    async def run(self, input_data):
        shared_store = {"input": input_data}
        
        # Sequential execution
        await self.validation_node.run(shared_store)
        await self.analysis_node.run(shared_store)
        await self.citation_node.run(shared_store)
        
        return shared_store["final_result"]
```

**Parallel Flow Pattern** (for complex workflows):
```python
class DocumentProcessingFlow(AsyncFlow):
    """Parallel processing for document analysis"""
    
    async def run(self, document_data):
        # Parallel Node execution
        tasks = [
            self.content_analysis_node.run(shared_store),
            self.reference_extraction_node.run(shared_store),
            self.theme_identification_node.run(shared_store)
        ]
        
        await asyncio.gather(*tasks)
        return self.combine_results(shared_store)
```

## Data Architecture

### Database Integration Pattern

**Connection Management**:
```python
from databases import Database

# Async database connections
database = Database("sqlite:///./theo.db")  # Development
# database = Database(os.getenv("SUPABASE_URL"))  # Production

class DatabaseMixin:
    """Mixin for Nodes requiring database access"""
    
    @property
    def db(self):
        return database
    
    async def ensure_connection(self):
        if not database.is_connected:
            await database.connect()
```

**Schema Management**:
- **SQLite**: Local development with `sqlite_schema.sql`
- **Supabase**: Production PostgreSQL with pgvector extension
- **Vector Storage**: Theological document embeddings for semantic search
- **Metadata Storage**: Document metadata, user data, processing status

### Data Models Architecture

**Core Data Models**:
```python
from pydantic import BaseModel
from typing import Optional, List

class User(BaseModel):
    id: str
    email: str
    role: str  # "user" | "admin"
    status: str  # "pending" | "approved" | "denied"
    created_at: datetime

class Document(BaseModel):
    id: str
    filename: str
    document_type: str  # "biblical" | "theological"
    processing_status: str  # "queued" | "processing" | "completed" | "failed"
    uploaded_by: str
    created_at: datetime

class TheologicalQuery(BaseModel):
    query: str
    context: Optional[str]
    user_id: str
    session_id: str
```

## Authentication & Authorization Architecture

### JWT-Based Authentication Pattern

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

### Role-Based Authorization

**Authorization Patterns**:
```python
def require_role(required_role: str):
    """Decorator for role-based access control"""
    def role_checker(current_user = Depends(verify_token)):
        if current_user.get("role") != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Usage in routes
@app.get("/api/admin/users")
async def get_users(admin_user = Depends(require_role("admin"))):
    # Admin-only endpoint implementation
```

## Background Processing Architecture

### Celery/Redis Integration

**Task Queue Architecture**:
```python
from celery import Celery

celery_app = Celery(
    "theo_workers",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def process_document_async(document_id: str):
    """Background document processing task"""
    # Initialize AsyncFlow for background processing
    flow = DocumentProcessingFlow()
    result = asyncio.run(flow.run({"document_id": document_id}))
    return result
```

**Progress Tracking via SSE**:
```python
@app.get("/api/progress/{task_id}")
async def stream_progress(task_id: str):
    """Server-Sent Events for progress updates"""
    
    async def event_stream():
        while not task_complete(task_id):
            progress = get_task_progress(task_id)
            yield f"data: {json.dumps(progress)}\n\n"
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_stream())
```

## Error Handling Architecture

### Node-Level Error Handling

**Graceful Error Recovery**:
```python
class RobustNode(AsyncNode):
    """Node with comprehensive error handling"""
    
    async def exec(self, data):
        try:
            return await self.process_data(data)
        except ValidationError as e:
            # Recoverable validation errors
            return {"error": "validation_failed", "details": str(e)}
        except ExternalServiceError as e:
            # Retry external service calls
            return await self.retry_with_backoff(data, max_retries=3)
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in {self.__class__.__name__}: {e}")
            return {"error": "processing_failed", "recoverable": False}
```

### API-Level Error Handling

**Consistent Error Responses**:
```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Invalid input data",
            "details": exc.errors()
        }
    )

@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "error": "authentication_failed", 
            "message": "Invalid credentials"
        }
    )
```

## Performance Architecture

### Caching Strategy

**Multi-Level Caching**:
```python
from functools import lru_cache
import redis

# In-memory caching for frequent operations
@lru_cache(maxsize=1000)
def get_theological_context(query: str):
    """Cache theological context lookups"""
    return expensive_context_operation(query)

# Redis caching for shared data
redis_client = redis.Redis(host='localhost', port=6379, db=1)

class CacheableNode(AsyncNode):
    """Node with Redis caching support"""
    
    async def exec(self, data):
        cache_key = f"node:{self.__class__.__name__}:{hash(str(data))}"
        
        # Check cache first
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Process and cache result
        result = await self.process_data(data)
        await redis_client.setex(cache_key, 3600, json.dumps(result))
        return result
```

### Connection Pooling

**Database Connection Management**:
```python
from databases import Database

# Connection pool configuration
database = Database(
    DATABASE_URL,
    min_size=5,    # Minimum connections
    max_size=20,   # Maximum connections
    max_queries=50000,  # Max queries per connection
    max_inactive_connection_lifetime=300  # 5 minutes
)
```

## Monitoring & Observability

### Health Check Architecture

**Comprehensive Health Monitoring**:
```python
class SystemHealthNode(AsyncNode):
    """Comprehensive system health validation"""
    
    async def exec(self, data):
        health_checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "external_apis": await self.check_external_services(),
            "disk_space": await self.check_disk_space(),
            "memory": await self.check_memory_usage()
        }
        
        overall_status = "ok" if all(health_checks.values()) else "degraded"
        
        return {
            "status": overall_status,
            "checks": health_checks,
            "timestamp": datetime.utcnow().isoformat()
        }
```

### Logging Architecture

**Structured Logging**:
```python
import logging
import json

class StructuredLogger:
    """JSON structured logging for PocketFlow Nodes"""
    
    @staticmethod
    def log_node_execution(node_name: str, execution_time: float, success: bool):
        logger.info(json.dumps({
            "event": "node_execution",
            "node": node_name,
            "execution_time_ms": execution_time * 1000,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }))
```

## Security Architecture

### Input Validation & Sanitization

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

### Rate Limiting

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