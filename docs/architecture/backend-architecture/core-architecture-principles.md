# Core Architecture Principles

## 1. PocketFlow-First Design
- **Node/Flow Pattern**: All AI workflows implemented as PocketFlow Nodes (≤150 lines) orchestrated by Flows
- **Async Processing**: AsyncNodes for I/O operations, AsyncFlows for complex orchestration
- **Shared Store Communication**: Nodes communicate exclusively via shared store patterns
- **Cookbook Compliance**: All implementations follow proven PocketFlow cookbook patterns

## 2. Modular Application Structure
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

## 3. Scalable Processing Architecture
- **Real-time Processing**: FastAPI endpoints trigger PocketFlow Flows for immediate responses
- **Background Processing**: Celery/Redis queue for long-running document processing workflows
- **Event-driven Updates**: Server-Sent Events (SSE) for real-time progress updates
