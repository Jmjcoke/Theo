# Theo - Theological Research System

## Project Overview
Theo is a theological research system built with PocketFlow architecture, providing RAG-powered chat capabilities for exploring scripture, church history, and systematic theology.

## Architecture
- **Frontend**: React/TypeScript (Port 8080)
- **Backend**: FastAPI/Python (Port 8001)
- **Framework**: PocketFlow for workflow orchestration
- **Database**: Supabase for document storage and vector search
- **AI**: OpenAI GPT-4 for generation and embeddings

## CRITICAL TESTING RULE

**ALWAYS USE BROWSER MCP FOR FINAL TESTING**

Direct API tests and custom test scripts often work when the actual user-facing system fails. The user experience through the browser is the ONLY reliable test of whether fixes actually work.

### Testing Protocol:
1. Make your code changes
2. Use Browser MCP to navigate to the actual interface 
3. Test the exact user workflow (login, navigate, interact)
4. Verify the fix works in the browser before declaring success

### Why Direct API Tests Mislead:
- API tests bypass frontend validation, error handling, and UI state management
- Browser tests reveal authentication issues, session management, timeout handling, and JavaScript errors
- Real user workflows include navigation, form submission, and state persistence that API tests miss

**Remember: If it doesn't work in the browser, it doesn't work for the user.**

## PROJECT PORT CONFIGURATION

**HARDCODED PORTS - DO NOT CHANGE**

- Frontend: http://localhost:8080 (React/Vite development server)
- Backend: http://localhost:8001 (FastAPI Python server)

These ports have been used throughout the entire project lifecycle. All configurations, environment variables, and documentation assume these ports. Do not suggest or use alternative ports.

## Development Commands

### Backend (Port 8001)
```bash
cd apps/api
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend (Port 8080)
```bash
cd apps/web
npm run dev -- --port 8080
```

### Testing
- Run comprehensive tests: `cd apps/api && python -m pytest`
- Lint/type check commands should be run after making code changes
- Always use Browser MCP for final validation

## PocketFlow Compliance
This project strictly adheres to PocketFlow patterns:
- AsyncNode methods: `prep_async()`, `exec_async()`, `post_async()`
- AsyncFlow for orchestrating async nodes
- Proper return types and signatures
- Shared store communication between nodes

## Key Features
- Document upload and processing pipeline
- Theological chat with source citations
- Admin dashboard for user and document management
- Real-time job status updates via SSE
- Advanced RAG pipeline with hermeneutics filtering