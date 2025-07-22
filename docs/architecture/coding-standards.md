# Coding Standards

**Note:** This section serves as the single, definitive source for all coding standards and naming conventions, fulfilling the PRD requirement for a "Naming Convention" document.

## PocketFlow Development Standards (CRITICAL)

**150-Line Node Limit (MANDATORY):**
- Every PocketFlow Node MUST NOT exceed 150 lines of code
- Use line counting tools: `wc -l {node_file}.py` must return ≤ 150
- Break complex logic into multiple Nodes if needed
- Validate Node size limits in pre-commit hooks and CI/CD

**PocketFlow Architecture Patterns:**
- **Nodes**: Single responsibility, stateless, communicates via shared store
- **Flows**: Orchestrate multiple Nodes, handle error recovery
- **AsyncNodes**: For I/O operations (API calls, database operations)
- **AsyncFlows**: For complex async workflow orchestration

**Cookbook Pattern Compliance:**
- ALWAYS reference PocketFlow cookbook examples before implementation
- Use proven patterns from `/PocketFlow-main/cookbook/` directory
- Document which cookbook pattern was adapted in code comments

**PocketFlow File Organization:**
- **Nodes**: `apps/api/src/nodes/{category}/{purpose}_node.py`
- **Flows**: `apps/api/src/flows/{workflow}_flow.py`
- **AsyncNodes**: `apps/workers/src/nodes/{category}/{purpose}_node.py`
- **AsyncFlows**: `apps/workers/src/flows/{workflow}_flow.py`

## Naming Conventions

**PocketFlow-Specific Naming:**
- Node files: `{purpose}_node.py` (e.g., `login_node.py`, `parse_node.py`)
- Flow files: `{workflow}_flow.py` (e.g., `auth_flow.py`, `chat_flow.py`)
- Node classes: `{Purpose}Node` (e.g., `LoginNode`, `ParseNode`)
- Flow classes: `{Workflow}Flow` (e.g., `AuthFlow`, `ChatFlow`)

**File and Directory Naming:**
- Use kebab-case for directories: `user-management`, `document-processing`
- Use PascalCase for React components: `UserDashboard.tsx`, `DocumentTable.tsx`
- Use camelCase for utility files: `apiClient.ts`, `dateUtils.ts`

**Variable and Function Naming:**
- Use camelCase for variables and functions: `userId`, `processingStatus`, `handleSubmit`
- Use PascalCase for types and interfaces: `User`, `DocumentMetadata`, `ProcessingResult`
- Use SCREAMING_SNAKE_CASE for constants: `MAX_FILE_SIZE`, `API_BASE_URL`

**Database Naming:**
- Use snake_case for table names: `users`, `document_metadata`, `processing_jobs`
- Use snake_case for column names: `user_id`, `created_at`, `processing_status`

**API Naming:**
- Use kebab-case for endpoints: `/api/user-management`, `/api/document-upload`
- Use camelCase for JSON keys: `userId`, `createdAt`, `processingStatus`

## PocketFlow Code Quality Standards

**Node Implementation Requirements:**
- Each Node must have prep/exec/post phases clearly defined
- Shared store communication must be documented
- Error handling and retry mechanisms required
- Unit tests for each Node phase mandatory

**Flow Composition Standards:**
- Flow must handle Node failures gracefully
- Async patterns must be used for I/O operations
- Flow execution must be monitorable via shared store
- Integration tests required for complete Flow execution

**Testing Requirements:**
- Node unit tests: Test prep/exec/post phases independently
- Flow integration tests: Test complete workflow execution
- Cookbook compliance tests: Validate against cookbook patterns
- Performance tests: Validate async execution times