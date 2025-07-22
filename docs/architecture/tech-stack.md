# Technology Stack

## Core Framework

### PocketFlow Architecture (v0.0.2)
- **Purpose**: Core LLM workflow orchestration framework
- **Pattern**: Node/Flow architecture for AI agent workflows
- **Location**: `/Users/joshuacoke/dev/Theo/PocketFlow-main/`
- **Installation**: `pip install -e ./PocketFlow-main`

**Key Principles**:
- **Node Limit**: Each Node must not exceed 150 lines of code
- **Stateless Nodes**: All nodes must be stateless and communicate via shared store
- **Async Patterns**: Nodes must implement async patterns where appropriate
- **Pattern Types**: Agent, Workflow, RAG, Map-Reduce, Supervisor patterns

## Backend Stack

### Core Application
- **Framework**: FastAPI 0.115.0
- **Server**: Uvicorn with standard features
- **Architecture**: PocketFlow Node/Flow patterns
- **Language**: Python 3.8+

### Database Layer
- **Local Development**: SQLite (metadata storage)
- **Production**: Supabase PostgreSQL with pgvector extension
- **Vector Database**: pgvector for embeddings and similarity search
- **ORM/Data Access**: Direct SQL with connection pooling

### Authentication & Security  
- **Authentication**: JWT tokens with bcrypt password hashing
- **Authorization**: Role-based access control (user/admin)
- **Security**: Input validation, rate limiting, CORS configuration

### AI/ML Integration
- **LLM Provider**: OpenAI API (GPT-4) with Anthropic Claude fallback
- **Embeddings**: OpenAI text-embedding-ada-002 (1536 dimensions)
- **Pattern**: PocketFlow workflow orchestration for all AI operations
- **Structured Output**: YAML format for LLM responses

### Background Processing
- **Task Queue**: Celery with Redis broker
- **Async Processing**: PocketFlow AsyncNode patterns
- **Real-time Updates**: Server-Sent Events (SSE)
- **WebSockets**: FastAPI WebSocket integration for chat

### Required Dependencies
```txt
# Core PocketFlow
pocketflow>=0.0.2

# FastAPI Stack  
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12
pydantic==2.10.2

# LLM Integration
openai>=1.0.0
anthropic>=0.8.0

# Async & HTTP
aiohttp>=3.8.0
aiofiles>=23.0.0

# Structured Output
PyYAML>=6.0

# Background Processing
celery>=5.3.0
redis>=4.5.0

# Vector Database
faiss-cpu>=1.7.0

# Testing
requests>=2.32.3
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

## Frontend Stack

### Core Application
- **Framework**: React 18.3.1 with TypeScript
- **Styling**: TailwindCSS with shadcn/ui components
- **Build Tool**: Vite
- **Package Manager**: npm

### State Management & Data Flow
- **API Communication**: Axios with interceptors
- **Real-time Updates**: WebSocket client for PocketFlow progress
- **State Management**: Zustand for workflow state tracking
- **Form Handling**: React Hook Form with validation

### UI/UX Framework
- **Component Library**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **Styling**: TailwindCSS with CSS variables
- **Responsive**: Mobile-first design approach

### Integration Patterns
- **PocketFlow Integration**: WebSocket/SSE for workflow progress
- **Error Boundaries**: React error boundaries for workflow failures
- **Loading States**: Progress indicators for async workflows
- **Real-time Updates**: Live status updates for background processes

## Development & Deployment

### Development Environment
- **IDE Support**: Cursor with PocketFlow .cursorrules
- **Code Quality**: ESLint + Prettier with PocketFlow patterns
- **Testing**: Pytest for backend, Jest for frontend
- **Documentation**: Markdown with BMAD system integration

### PocketFlow Development Patterns
- **Node Development**: Follow 150-line limit with prep/exec/post pattern
- **Flow Composition**: Use cookbook examples as templates
- **Async Patterns**: AsyncNode for I/O operations, AsyncFlow for orchestration
- **Error Handling**: Node retry mechanisms with graceful fallbacks

### Deployment Architecture
- **Backend**: FastAPI application with PocketFlow workflows
- **Frontend**: Static build deployed separately
- **Database**: SQLite for development, Supabase for production
- **Background Jobs**: Celery workers for PocketFlow async operations

## PocketFlow Pattern Implementation

### Available Cookbook Patterns
- **RAG Pattern**: `pocketflow-rag/` for document processing
- **Agent Pattern**: `pocketflow-agent/` for decision workflows
- **Workflow Pattern**: `pocketflow-fastapi-background/` for job processing  
- **Chat Pattern**: `pocketflow-fastapi-websocket/` for real-time chat
- **Structured Output**: `pocketflow-structured-output/` for hermeneutics

### Implementation Guidelines
- **Node Size**: Maximum 150 lines per Node
- **Shared State**: Use shared store for Node communication
- **Error Handling**: Leverage Node retry mechanisms
- **Testing**: Test prep/exec/post phases independently
- **Documentation**: Document Node purpose and data flow

This technology stack provides the foundation for implementing Theo as a PocketFlow-based theological AI assistant with proper workflow orchestration and scalable architecture patterns.