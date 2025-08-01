# Tasks / Subtasks
- [x] Task 1: Create Document Upload PocketFlow Nodes (AC: 1, 2, 3)
  - [x] Subtask 1.1: Create DocumentValidationNode for file and metadata validation (≤150 lines)
  - [x] Subtask 1.2: Create DocumentStorageNode for file storage and database record creation (≤150 lines)
  - [x] Subtask 1.3: Create JobDispatchNode for Celery background job creation (≤150 lines)
  - [x] Subtask 1.4: Test all three nodes independently for PocketFlow compliance

- [x] Task 2: Create Document Upload Flow Orchestration (AC: 4, 5)
  - [x] Subtask 2.1: Create DocumentUploadFlow to orchestrate the three nodes
  - [x] Subtask 2.2: Implement proper error handling and rollback mechanisms
  - [x] Subtask 2.3: Add shared store communication patterns between nodes
  - [x] Subtask 2.4: Test complete flow with mock file uploads

- [x] Task 3: Create FastAPI Admin Upload Endpoint (AC: 1, 5)
  - [x] Subtask 3.1: Create protected `/api/admin/upload` endpoint with admin role validation
  - [x] Subtask 3.2: Implement multipart/form-data file upload handling
  - [x] Subtask 3.3: Integrate FastAPI endpoint with DocumentUploadFlow
  - [x] Subtask 3.4: Add proper HTTP response formatting and error handling

- [x] Task 4: Database Schema and Models Integration (AC: 3)
  - [x] Subtask 4.1: Verify `documents` table schema supports required fields
  - [x] Subtask 4.2: Create Pydantic models for upload request/response
  - [x] Subtask 4.3: Implement database record creation with `queued` status
  - [x] Subtask 4.4: Add proper UUID generation for document IDs
