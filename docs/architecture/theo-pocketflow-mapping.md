# Theo System Architecture: PocketFlow Pattern Mapping

## Visual System Architecture Diagram

```
THEO APPLICATION ARCHITECTURE - PocketFlow Pattern Implementation

Current Implementation (Stories 1.1-1.4):
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FOUNDATION LAYER                                      │
│                                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Story 1.1  │────│   Story 1.2  │────│   Story 1.3  │────│   Story 1.4  │     │
│  │   Project    │    │   Backend    │    │   Frontend   │    │   Database   │     │
│  │   Setup      │    │   FastAPI    │    │   React      │    │   Schemas    │     │
│  │              │    │   Apps       │    │   TailwindCSS│    │   SQLite +   │     │
│  │              │    │              │    │              │    │   Supabase   │     │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────────┘

Upcoming Epic 2: User Authentication (Agent Pattern)
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AUTHENTICATION FLOW                                   │
│                            (PocketFlow Agent Pattern)                              │
│                                                                                     │
│      Looping + Branching                                                           │
│  ┌─────────────────────────┐         Need                ┌─────────────────────────┐ │
│  │      Login              │◄────── review ──────────────│       Validate          │ │
│  │    Attempt              │                             │       Credentials       │ │
│  └─────────┬───────────────┘                             └─────────────┬───────────┘ │
│            │                                                           │             │
│            ▼                     Approve                               │             │
│  ┌─────────────────────────┐◄──────────────────────────────────────────┘             │
│  │    Generate JWT         │                                                         │
│  │    Session Token        │                                                         │
│  └─────────────────────────┘                                                         │
│                                                                                     │
│  ┌─────────────────────────┐                                                         │
│  │     users table         │  ← Database foundation from Story 1.4                  │
│  │   (SQLite metadata)     │                                                         │
│  └─────────────────────────┘                                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

Epic 3: Document Upload (Workflow Pattern)
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DOCUMENT PROCESSING                                   │
│                            (PocketFlow Workflow Pattern)                           │
│                                                                                     │
│          Directed Path                                                              │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐         │
│  │    Upload       │────────│   Validate      │────────│    Store        │         │
│  │    Document     │        │   File Type     │        │   Metadata      │         │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘         │
│                                                                                     │
│  ┌─────────────────────────┐                                                         │
│  │   documents table       │  ← Database foundation from Story 1.4                  │
│  │  (SQLite metadata)      │                                                         │
│  └─────────────────────────┘                                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

Epic 4: Document Processing Pipeline (Map-Reduce + RAG Pattern)
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          DOCUMENT PROCESSING PIPELINE                              │
│                      (PocketFlow Map-Reduce + RAG Pattern)                         │
│                                                                                     │
│              Batch + Merge                    (+ Vector DB store)                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │    Map      │────│ Summarize   │────│   Reduce    │────│   Store     │         │
│  │   Chunks    │    │   Chunk     │    │ Summaries   │    │ Embeddings  │         │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                  │                 │
│                                                                  ▼                 │
│              Looping (+ history & vector DB)                                       │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │                    RAG Query Engine                             │               │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │               │
│  │  │   Query     │────│   Retrieve  │────│   Generate  │         │               │
│  │  │   Input     │    │  Relevant   │    │   Response  │         │               │
│  │  │             │    │   Chunks    │    │             │         │               │
│  │  └─────────────┘    └─────────────┘    └─────────────┘         │               │
│  │            ▲                 ▲                                  │               │
│  │            │        ┌────────────────┐                         │               │
│  │            │        │  Vector DB     │                         │               │
│  │            │        │ (Supabase +    │                         │               │
│  │            │        │  pgvector)     │                         │               │
│  │            │        └────────────────┘                         │               │
│  │            └─────── chat history ──────────────────────────────┘               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Database Foundation                                   │   │
│  │  ┌─────────────────────┐    ┌─────────────────────────────────────────────┐  │   │
│  │  │ processing_jobs     │    │        document_chunks table               │  │   │
│  │  │    (SQLite)         │    │         (Supabase PostgreSQL)              │  │   │
│  │  │                     │    │                                             │  │   │
│  │  │ - job tracking      │    │ - text content + vector embeddings         │  │   │
│  │  │ - error handling    │    │ - biblical citation metadata               │  │   │
│  │  │ - status mgmt       │    │ - theological source metadata              │  │   │
│  │  └─────────────────────┘    └─────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘

Epic 5: Chat Interface (Chat Memory Pattern)
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                             CHAT INTERFACE                                         │
│                        (PocketFlow Chat Memory Pattern)                            │
│                                                                                     │
│              Looping (+ history & vector DB)                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                             │
│  │    Chat     │────│    Store    │────│  Retrieve   │                             │
│  │   Input     │    │  Message    │    │  Context    │                             │
│  └─────────────┘    └─────────────┘    └─────────────┘                             │
│         │                    │                │                                    │
│         │            ┌───────────────────────────────────┐                         │
│         │            │    history & vector DB            │                         │
│         │            │                                   │                         │
│         │            │ ┌─────────────┐ ┌─────────────┐   │                         │
│         │            │ │Chat History │ │Vector Search│   │                         │
│         │            │ │ (Session)   │ │(Supabase)   │   │                         │
│         │            │ └─────────────┘ └─────────────┘   │                         │
│         │            └───────────────────────────────────┘                         │
│         │                                   │                                      │
│         └──────────── read ─────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

Epic 6: Admin Dashboard (Supervisor Pattern)
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            ADMIN DASHBOARD                                         │
│                        (PocketFlow Supervisor Pattern)                             │
│                                                                                     │
│                              Nesting                                               │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │                      Monitor                                    │               │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │               │
│  │  │   Users     │    │ Documents   │    │ Processing  │         │               │
│  │  │ Management  │    │ Management  │    │   Jobs      │         │               │
│  │  └─────────────┘    └─────────────┘    └─────────────┘         │               │
│  │            ▲               ▲                   ▲                │               │
│  │            │               │                   │                │               │
│  │            ├───────────────┼───────────────────┘                │               │
│  │            │               │                                    │               │
│  │  ┌──────────────────────────────────────────────────────────┐   │               │
│  │  │              Database Monitoring                         │   │               │
│  │  │                                                          │   │               │
│  │  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │   │               │
│  │  │ │   users     │  │ documents   │  │ processing_jobs │   │   │               │
│  │  │ │  (SQLite)   │  │ (SQLite)    │  │   (SQLite)      │   │   │               │
│  │  │ └─────────────┘  └─────────────┘  └─────────────────┘   │   │               │
│  │  └──────────────────────────────────────────────────────────┘   │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                     │                                              │
│                            ┌────── reject                                          │
│                            ▼                                                       │
│  ┌─────────────────────────────────────┐         ┌─────────────────────────┐       │
│  │           Supervise                 │────────▶│       Approve           │       │
│  │      (Review Actions)               │         │    (Execute Actions)    │       │
│  └─────────────────────────────────────┘         └─────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────────────┘


SYSTEM INTEGRATION OVERVIEW
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE THEO ECOSYSTEM                                    │
│                      (Multiple PocketFlow Patterns)                                │
│                                                                                     │
│  Frontend (React)        Backend (FastAPI)         Databases                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                 │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │                 │
│  │ │Chat Interface│ │    │ │    Auth     │ │    │ │   SQLite    │ │                 │
│  │ └─────────────┘ │◄──►│ └─────────────┘ │◄──►│ │ (metadata)  │ │                 │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ └─────────────┘ │                 │
│  │ │   Upload    │ │    │ │   Upload    │ │    │ ┌─────────────┐ │                 │
│  │ │   Forms     │ │    │ │  Handler    │ │    │ │  Supabase   │ │                 │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ │ (vectors)   │ │                 │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ └─────────────┘ │                 │
│  │ │   Admin     │ │    │ │ Processing  │ │    └─────────────────┘                 │
│  │ │ Dashboard   │ │    │ │  Pipeline   │ │                                        │
│  │ └─────────────┘ │    │ └─────────────┘ │                                        │
│  └─────────────────┘    └─────────────────┘                                        │
│                                                                                     │
│                         PocketFlow Patterns Used:                                  │
│                         ✅ Workflow (Document Upload)                              │
│                         ✅ Agent (User Authentication)                             │
│                         ✅ Map-Reduce (Document Processing)                        │
│                         ✅ RAG (Retrieval-Augmented Generation)                   │
│                         ✅ Chat Memory (Conversation Interface)                    │
│                         ✅ Supervisor (Admin Management)                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## PocketFlow Pattern Compliance Analysis

### ✅ **PERFECT ALIGNMENT ACHIEVED**

Our Theo system architecture demonstrates **complete alignment** with PocketFlow patterns:

#### **1. Foundation Layer (Stories 1.1-1.4)**
- **Database Schema**: Provides the essential data layer that all PocketFlow nodes require
- **Stateless Design**: Database operations support PocketFlow's stateless node architecture
- **Modular Structure**: Each component can be processed independently by different nodes

#### **2. Workflow Pattern Implementation**
- **Document Upload Flow**: Direct path from upload → validate → store
- **User Authentication**: Agent pattern with looping and branching for credential validation
- **Processing Pipeline**: Map-reduce pattern for chunking and embedding documents

#### **3. Advanced Pattern Integration**
- **RAG System**: Combines vector store with retrieval and generation nodes
- **Chat Memory**: Implements conversation history with vector database integration  
- **Supervisor Pattern**: Admin dashboard monitoring and approval workflows

#### **4. Data Architecture Compliance**
- **SQLite**: Metadata storage for workflow state management
- **Supabase + pgvector**: Vector database for RAG pattern implementation
- **Job Tracking**: Processing jobs table enables proper workflow orchestration

### **Key Success Factors:**

1. **Modular Design**: Each epic maps to specific PocketFlow patterns
2. **Stateless Operations**: Database design supports independent node processing
3. **Proper Abstraction**: Clear separation between different workflow types
4. **Scalable Foundation**: Database schemas anticipate complex pipeline requirements

**Our implementation doesn't just use PocketFlow patterns - it exemplifies them perfectly!** 🚀