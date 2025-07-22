# Unified Project Structure

## Purpose

This document defines the unified organizational structure for the entire Theo project, ensuring consistency across all development workflows, BMAD agent operations, and PocketFlow pattern implementations.

## Project Organization Philosophy

Theo follows a **PocketFlow-First Architecture** with **BMAD Workflow Integration**, where:

1. **Every component** follows PocketFlow's 150-line Node limit
2. **Every workflow** uses proven cookbook patterns  
3. **Every development task** is guided by BMAD agents
4. **Every file** has a clear purpose and location

## Unified Directory Structure

### Root Level Organization
```
/Users/joshuacoke/dev/Theo/
│
├── 📁 .bmad-core/                 # BMAD Development Workflow System
│   ├── agents/                    # Agent configurations (dev, qa, sm, etc.)
│   ├── templates/                 # Story and document templates
│   ├── checklists/               # Definition of Done checklists
│   ├── tasks/                    # BMAD task definitions
│   ├── data/                     # Development guidance and patterns
│   └── core-config.yaml          # BMAD system configuration
│
├── 📁 .cursorrules               # PocketFlow development rules
├── 📁 .github/                   # GitHub Actions and workflows  
│   └── workflows/                # CI/CD pipeline definitions
│
├── 📁 PocketFlow-main/           # PocketFlow Framework Source (v0.0.2)
│   ├── pocketflow/               # Core framework code
│   ├── cookbook/                 # Pattern implementation examples
│   ├── docs/                     # Framework documentation
│   └── setup.py                 # Framework installation
│
├── 📁 apps/                      # Application Modules
│   ├── api/                     # Backend API application
│   ├── web/                     # Frontend web application  
│   └── workers/                 # Background processing workers
│
├── 📁 docs/                      # Project Documentation
│   ├── architecture/            # Technical architecture docs
│   ├── prd/                     # Product requirements (sharded)
│   └── stories/                 # Development stories
│
├── 📁 infrastructure/            # Deployment and DevOps
├── 📁 packages/                  # Shared npm packages
├── 📁 tests/                     # Cross-application testing
└── 📁 web-bundles/               # BMAD agent bundle configurations
```

### Backend Application Structure (`apps/api/`)
```
apps/api/
│
├── 📁 src/                       # Source Code (PocketFlow Architecture)
│   ├── 📁 nodes/                 # PocketFlow Node Implementations (≤150 lines each)
│   │   ├── auth/                 # Authentication processing nodes
│   │   │   ├── login_node.py     # User login validation
│   │   │   ├── register_node.py  # User registration processing
│   │   │   └── jwt_node.py       # JWT token management
│   │   ├── chat/                 # Real-time chat processing nodes
│   │   │   ├── message_node.py   # Message processing
│   │   │   ├── context_node.py   # Context management
│   │   │   └── response_node.py  # Response generation
│   │   ├── documents/            # Document analysis nodes
│   │   │   ├── upload_node.py    # Document upload handling
│   │   │   ├── parse_node.py     # Content parsing
│   │   │   └── analyze_node.py   # Content analysis
│   │   └── workflows/            # Workflow orchestration nodes
│   │       ├── hermeneutic_node.py # Theological analysis
│   │       ├── citation_node.py    # Biblical citation processing
│   │       └── summary_node.py     # Content summarization
│   │
│   ├── 📁 flows/                 # PocketFlow Flow Compositions
│   │   ├── auth_flow.py          # Authentication workflows
│   │   ├── chat_flow.py          # Chat interaction workflows
│   │   ├── document_flow.py      # Document processing workflows
│   │   └── hermeneutic_flow.py   # Theological analysis workflows
│   │
│   ├── 📁 utils/                 # Utility Functions (Node Support)
│   │   ├── llm_utils.py          # LLM integration utilities
│   │   ├── vector_utils.py       # Vector database utilities
│   │   ├── async_utils.py        # Async processing utilities
│   │   └── testing.py            # Testing helper functions
│   │
│   ├── 📁 examples/              # Cookbook Pattern Adaptations
│   │   ├── cookbook/             # Direct cookbook implementations
│   │   │   ├── rag/              # RAG pattern (pocketflow-rag)
│   │   │   ├── agent/            # Agent pattern (pocketflow-agent)
│   │   │   ├── websocket/        # WebSocket chat (pocketflow-fastapi-websocket)
│   │   │   ├── background/       # Background jobs (pocketflow-fastapi-background)
│   │   │   └── structured/       # Structured output (pocketflow-structured-output)
│   │   └── theo_specific/        # Theo-adapted patterns
│   │       ├── theological_agent.py    # Theo agent pattern
│   │       ├── biblical_rag.py         # Biblical text RAG
│   │       └── hermeneutic_workflow.py # Hermeneutic analysis
│   │
│   ├── 📁 api/                   # FastAPI Route Definitions
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── chat.py               # Chat endpoints
│   │   ├── documents.py          # Document endpoints
│   │   └── workflows.py          # Workflow endpoints
│   │
│   ├── 📁 core/                  # Core Application Logic
│   │   ├── config.py             # Application configuration
│   │   ├── database.py           # Database connection management
│   │   └── middleware.py         # Request/response middleware
│   │
│   └── 📁 admin/                 # Admin Interface Logic
│       ├── users.py              # User management
│       ├── documents.py          # Document management
│       └── analytics.py          # System analytics
│
├── 📁 database/                  # Database Schemas and Migrations
│   ├── sqlite_schema.sql         # Local development schema
│   ├── supabase_schema.sql       # Production schema (Supabase)
│   ├── migrations/               # Database migration scripts
│   └── test_schemas.py           # Schema validation tests
│
├── 📁 tests/                     # Testing Structure
│   ├── nodes/                    # Node unit tests
│   ├── flows/                    # Flow integration tests
│   ├── api/                      # API endpoint tests
│   ├── integration/              # Full integration tests
│   └── fixtures/                 # Test data and fixtures
│
├── requirements.txt              # Python dependencies (includes PocketFlow)
├── main.py                       # FastAPI application entry point
├── start.sh                      # Local development startup script
└── README.md                     # Backend setup instructions
```

### Frontend Application Structure (`apps/web/`)
```
apps/web/
│
├── 📁 src/                       # React Source Code
│   ├── 📁 components/            # React Components
│   │   ├── chat/                 # Chat interface components
│   │   │   ├── ChatInterface.tsx # Main chat component
│   │   │   ├── MessageList.tsx   # Message display
│   │   │   └── MessageInput.tsx  # Message input
│   │   ├── documents/            # Document management components
│   │   │   ├── DocumentUpload.tsx # Document upload interface
│   │   │   ├── DocumentList.tsx   # Document listing
│   │   │   └── DocumentViewer.tsx # Document display
│   │   ├── workflow/             # Workflow status components
│   │   │   ├── WorkflowStatus.tsx # Flow status display
│   │   │   └── ProgressBar.tsx    # Progress indication
│   │   └── common/               # Shared UI components
│   │       ├── Layout.tsx        # Application layout
│   │       ├── Navigation.tsx    # Navigation components
│   │       └── LoadingSpinner.tsx # Loading indicators
│   │
│   ├── 📁 pages/                 # Page-Level Components
│   │   ├── Index.tsx             # Landing page
│   │   ├── ChatInterface.tsx     # Chat page
│   │   ├── LoginPage.tsx         # Authentication page
│   │   └── NotFound.tsx          # 404 error page
│   │
│   ├── 📁 services/              # API Service Integrations
│   │   ├── api.ts                # REST API service
│   │   ├── websocket.ts          # WebSocket service (PocketFlow flows)
│   │   ├── sse.ts                # Server-Sent Events (background jobs)
│   │   └── auth.ts               # Authentication service
│   │
│   ├── 📁 stores/                # State Management (Zustand)
│   │   ├── chatStore.ts          # Chat state management
│   │   ├── authStore.ts          # Authentication state
│   │   ├── documentStore.ts      # Document management state
│   │   └── workflowStore.ts      # Workflow status state
│   │
│   ├── 📁 hooks/                 # React Custom Hooks
│   │   ├── useWebSocket.ts       # WebSocket management
│   │   ├── useAuth.ts            # Authentication hook
│   │   └── useWorkflowStatus.ts  # Workflow status tracking
│   │
│   └── 📁 utils/                 # Frontend Utilities
│       ├── formatters.ts         # Data formatting utilities
│       ├── validators.ts         # Form validation
│       └── constants.ts          # Application constants
│
├── 📁 tests/                     # Frontend Testing
│   ├── components/               # Component tests
│   ├── pages/                    # Page tests
│   ├── services/                 # Service tests
│   └── e2e/                      # End-to-end tests
│
├── 📁 public/                    # Static Assets
├── package.json                  # NPM dependencies and scripts
├── vite.config.ts               # Vite build configuration
├── tailwind.config.ts           # TailwindCSS configuration
└── README.md                    # Frontend setup instructions
```

### Background Workers Structure (`apps/workers/`)
```
apps/workers/
│
├── 📁 src/                       # Worker Source Code
│   ├── 📁 nodes/                 # AsyncNode Implementations (≤150 lines each)
│   │   ├── document_processing/  # Document analysis async nodes
│   │   │   ├── ocr_node.py       # OCR processing
│   │   │   ├── nlp_node.py       # NLP analysis
│   │   │   └── index_node.py     # Vector indexing
│   │   ├── vector_indexing/      # Vector database async nodes
│   │   │   ├── embed_node.py     # Embedding generation
│   │   │   ├── store_node.py     # Vector storage
│   │   │   └── search_node.py    # Vector search
│   │   └── notification/         # Notification async nodes
│   │       ├── email_node.py     # Email notifications
│   │       ├── webhook_node.py   # Webhook notifications
│   │       └── sse_node.py       # Server-sent event notifications
│   │
│   ├── 📁 flows/                 # AsyncFlow Compositions
│   │   ├── document_pipeline.py  # Document processing pipeline
│   │   ├── vector_pipeline.py    # Vector indexing pipeline
│   │   └── notification_flow.py  # Notification delivery flow
│   │
│   └── 📁 tasks/                 # Celery Task Definitions
│       ├── document_tasks.py     # Document processing tasks
│       ├── vector_tasks.py       # Vector operations tasks
│       └── notification_tasks.py # Notification tasks
│
├── 📁 tests/                     # Worker Testing
│   ├── nodes/                    # AsyncNode tests
│   ├── flows/                    # AsyncFlow tests
│   └── tasks/                    # Task tests
│
├── requirements.txt              # Worker-specific dependencies
└── main.py                      # Worker entry point
```

## Documentation Organization (`docs/`)

### Architecture Documentation
```
docs/architecture/
├── index.md                     # Architecture overview
├── introduction.md              # Project introduction  
├── high-level-architecture.md   # System design overview
├── tech-stack.md               # Technology stack (PocketFlow-focused)
├── source-tree.md              # This unified structure document
├── testing-strategy.md         # Testing approaches and patterns
├── unified-project-structure.md # Project organization (this document)
├── coding-standards.md         # Development standards and guidelines
└── theo-pocketflow-mapping.md  # PocketFlow pattern implementation mapping
```

### Product Requirements Documentation (Sharded)
```
docs/prd/
├── index.md                              # PRD overview and navigation
├── goals-and-background-context.md      # Project context and objectives
├── requirements.md                      # Functional and non-functional requirements
├── technical-assumptions.md             # Technical decisions and constraints
├── user-interface-design-goals.md       # UI/UX design principles
├── project-glossary-and-data-dictionary.md # Terminology and data definitions
├── project-principles-and-lessons-learned.md # Development principles
└── epic-and-story-details.md           # Epic breakdown and story details
```

### Development Stories
```
docs/stories/
├── 1.1.project-initialization.md        # BMAD setup and project structure
├── 1.2.backend-app-setup.md            # FastAPI backend initialization
├── 1.3.frontend-app-setup.md           # React frontend initialization
├── 1.4.database-schema-initialization.md # Database schema setup
└── [future stories...]                  # Additional development stories
```

## File Naming Conventions

### PocketFlow Node Files
- **Pattern**: `{purpose}_node.py` (e.g., `login_node.py`, `parse_node.py`)
- **Line Limit**: Maximum 150 lines per file
- **Location**: `apps/api/src/nodes/{category}/`

### PocketFlow Flow Files  
- **Pattern**: `{workflow}_flow.py` (e.g., `auth_flow.py`, `chat_flow.py`)
- **Location**: `apps/api/src/flows/` or `apps/workers/src/flows/`

### React Component Files
- **Pattern**: `{ComponentName}.tsx` (PascalCase)
- **Location**: `apps/web/src/components/{category}/`

### Test Files
- **Pattern**: `test_{module_name}.py` or `{ComponentName}.test.tsx`
- **Location**: Mirrored structure in corresponding `tests/` directory

## Cross-Application Integration Points

### API Endpoints → PocketFlow Flows
```
Frontend Request → FastAPI Endpoint → PocketFlow Flow → AsyncNodes → Response
```

### Real-time Communication
```
WebSocket Connection → Flow Status Updates → Frontend State Updates
```

### Background Processing
```
User Action → Background Job → AsyncFlow → Celery Tasks → Notifications
```

## Development Workflow Integration

### BMAD Agent File Dependencies
**Files that BMAD agents reference (from `core-config.yaml`):**
- ✅ `docs/architecture/coding-standards.md`
- ✅ `docs/architecture/tech-stack.md`  
- ✅ `docs/architecture/source-tree.md`
- ✅ `docs/architecture/testing-strategy.md`
- ✅ `docs/architecture/unified-project-structure.md` (this document)

### Story Creation Workflow
1. **SM Agent** creates story using templates in `.bmad-core/templates/`
2. **Dev Agent** references architecture docs for implementation
3. **QA Agent** validates using checklists in `.bmad-core/checklists/`
4. **All agents** follow PocketFlow patterns from cookbook examples

### Code Quality Gates
- **150-line Node limit** enforced by linting and code review
- **PocketFlow pattern compliance** validated by QA agent
- **Cookbook pattern adherence** checked against examples
- **BMAD workflow completion** tracked through story lifecycle

This unified project structure ensures that every file, component, and workflow has a clear place and purpose within the Theo project's PocketFlow-first, BMAD-managed development approach.