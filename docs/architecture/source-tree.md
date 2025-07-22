# Source Tree Structure

## Project Architecture Overview

Theo is organized as a monorepo with PocketFlow-compliant architecture patterns. The structure enforces the 150-line Node limit and follows proven cookbook patterns for AI workflow orchestration.

## Root Level Structure

```
/Users/joshuacoke/dev/Theo/
├── .bmad-core/                    # BMAD development workflow system
├── .cursorrules                   # PocketFlow development guidance (from cookbook)
├── PocketFlow-main/               # PocketFlow framework source (v0.0.2)
├── apps/                          # Application modules
├── docs/                          # Project documentation
├── packages/                      # Shared packages
├── infrastructure/               # Deployment configurations
└── web-bundles/                  # BMAD agent configurations
```

## Application Structure (`apps/`)

### Backend API (`apps/api/`)

**PocketFlow-Compliant Structure:**
```
apps/api/
├── src/
│   ├── nodes/                     # PocketFlow Node implementations (150-line limit)
│   │   ├── auth/                  # Authentication nodes
│   │   ├── chat/                  # Chat processing nodes
│   │   ├── documents/             # Document processing nodes
│   │   └── workflows/             # Workflow orchestration nodes
│   ├── flows/                     # PocketFlow Flow compositions
│   │   ├── auth_flow.py           # User authentication flows
│   │   ├── chat_flow.py           # Real-time chat flows
│   │   ├── document_flow.py       # Document processing flows
│   │   └── hermeneutic_flow.py    # Theological analysis flows
│   ├── utils/                     # Utility functions for nodes
│   │   ├── llm_utils.py          # LLM integration utilities
│   │   ├── vector_utils.py       # Vector database utilities
│   │   └── async_utils.py        # Async processing utilities
│   ├── examples/                  # Cookbook example adaptations
│   │   ├── cookbook/             # Direct cookbook implementations
│   │   │   ├── rag/              # RAG pattern implementation
│   │   │   ├── agent/            # Agent pattern implementation
│   │   │   ├── websocket/        # WebSocket chat implementation
│   │   │   └── background/       # Background job implementation
│   │   └── theo_specific/        # Theo-adapted patterns
│   ├── api/                      # FastAPI route definitions
│   ├── core/                     # Core application logic
│   ├── admin/                    # Admin interface logic
│   └── auth/                     # Authentication logic
├── database/                     # Database schemas and migrations
│   ├── sqlite_schema.sql         # Local development schema
│   ├── supabase_schema.sql       # Production schema
│   └── migrations/               # Database migrations
├── requirements.txt              # Python dependencies (includes PocketFlow)
└── main.py                       # FastAPI application entry point
```

### Frontend Web (`apps/web/`)

**React + PocketFlow Integration Structure:**
```
apps/web/
├── src/
│   ├── components/               # React components
│   │   ├── chat/                # Chat interface components
│   │   ├── documents/           # Document management components
│   │   └── workflow/            # Workflow status components
│   ├── pages/                   # Page-level components
│   ├── services/                # API service integrations
│   │   ├── websocket.ts         # WebSocket service for PocketFlow flows
│   │   ├── sse.ts              # Server-Sent Events for background jobs
│   │   └── api.ts              # REST API service
│   ├── stores/                  # State management (Zustand)
│   ├── hooks/                   # React hooks
│   └── utils/                   # Frontend utilities
├── public/                      # Static assets
├── package.json                 # NPM dependencies
└── vite.config.ts              # Vite configuration
```

### Background Workers (`apps/workers/`)

**PocketFlow AsyncNode Structure:**
```
apps/workers/
├── src/
│   ├── nodes/                   # AsyncNode implementations for background jobs
│   │   ├── document_processing/ # Document analysis async nodes
│   │   ├── vector_indexing/     # Vector database indexing nodes
│   │   └── notification/        # Notification async nodes
│   ├── flows/                   # AsyncFlow compositions
│   │   ├── document_pipeline.py # Document processing pipeline
│   │   ├── vector_pipeline.py   # Vector indexing pipeline
│   │   └── notification_flow.py # Notification flow
│   └── tasks/                   # Celery task definitions
├── requirements.txt             # Worker-specific dependencies
└── main.py                     # Worker entry point
```

## Documentation Structure (`docs/`)

**BMAD-Compliant Documentation:**
```
docs/
├── architecture/                # Architectural documentation
│   ├── index.md                # Architecture overview
│   ├── introduction.md         # Project introduction
│   ├── high-level-architecture.md # System design
│   ├── tech-stack.md           # Technology stack (PocketFlow-focused)
│   ├── source-tree.md          # This document
│   ├── testing-strategy.md     # Testing approaches
│   ├── unified-project-structure.md # Project organization
│   ├── coding-standards.md     # Development standards
│   └── theo-pocketflow-mapping.md # PocketFlow pattern mapping
├── prd/                        # Product Requirements (sharded)
│   ├── index.md               # PRD overview
│   ├── goals-and-background-context.md
│   ├── requirements.md
│   ├── technical-assumptions.md
│   ├── user-interface-design-goals.md
│   ├── project-glossary-and-data-dictionary.md
│   ├── project-principles-and-lessons-learned.md
│   └── epic-and-story-details.md
├── stories/                    # Development stories
│   ├── 1.1.project-initialization.md
│   ├── 1.2.backend-app-setup.md
│   ├── 1.3.frontend-app-setup.md
│   └── 1.4.database-schema-initialization.md
├── front-end-spec.md          # Frontend specifications
├── fullstack-architecture.md  # Full-stack design
└── prd.md                     # Combined PRD reference
```

## PocketFlow Framework Integration (`PocketFlow-main/`)

**Available Cookbook Patterns:**
```
PocketFlow-main/cookbook/
├── pocketflow-rag/             # Document processing pattern → Epic 4
├── pocketflow-agent/           # Decision-making pattern → Epic 5
├── pocketflow-fastapi-background/ # Job processing → Epic 3
├── pocketflow-fastapi-websocket/  # Real-time chat → Epic 6
├── pocketflow-structured-output/  # Hermeneutics → Epic 7
├── pocketflow-workflow/        # Complex workflows → Epic 8
└── pocketflow-map-reduce/      # Batch processing → Data migration
```

## BMAD System Integration (`.bmad-core/`)

**Development Workflow System:**
```
.bmad-core/
├── agents/                     # Agent configurations
│   ├── dev.md                 # Developer agent (PocketFlow-enhanced)
│   ├── qa.md                  # QA agent (Pattern validation)
│   └── sm.md                  # Scrum Master (Story creation)
├── templates/                  # Story and document templates
├── checklists/                # Definition of Done checklists
├── tasks/                     # BMAD task definitions
├── data/                      # Development guidance
└── core-config.yaml           # BMAD configuration (references this structure)
```

## Development Workflow File Dependencies

**Files Required by BMAD (`core-config.yaml` `devLoadAlwaysFiles`):**
- `docs/architecture/coding-standards.md` ✅
- `docs/architecture/tech-stack.md` ✅
- `docs/architecture/source-tree.md` ✅ (This document)
- `docs/architecture/testing-strategy.md` ⏳ (Next to create)
- `docs/architecture/unified-project-structure.md` ⏳ (To be created)

## PocketFlow Pattern Implementation Guidelines

### Node Implementation Locations
- **Authentication Nodes**: `apps/api/src/nodes/auth/`
- **Chat Processing Nodes**: `apps/api/src/nodes/chat/`
- **Document Analysis Nodes**: `apps/api/src/nodes/documents/`
- **Workflow Orchestration Nodes**: `apps/api/src/nodes/workflows/`

### Flow Composition Locations
- **User-facing Flows**: `apps/api/src/flows/`
- **Background Processing Flows**: `apps/workers/src/flows/`
- **Integration Testing Flows**: `apps/api/tests/flows/`

### Key Principles for File Organization
1. **150-Line Node Limit**: Each Node file must not exceed 150 lines
2. **Single Responsibility**: Each Node handles one specific task
3. **Async Patterns**: AsyncNodes for I/O operations, AsyncFlows for orchestration
4. **Cookbook Compliance**: Follow proven patterns from PocketFlow cookbook
5. **Shared State**: Use shared store for Node-to-Node communication

This source tree structure ensures that all BMAD agents have clear guidance for file placement while maintaining PocketFlow architectural patterns and 150-line Node limits throughout the development process.