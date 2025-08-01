# Testing

## Testing Standards
**Test File Locations**:
- Node tests: `apps/api/tests/nodes/documents/test_*.py`
- Flow tests: `apps/api/tests/flows/test_document_upload_flow.py`
- API tests: `apps/api/tests/api/test_document_routes.py`
- Integration tests: `apps/api/tests/integration/test_document_upload.py`

**Testing Frameworks**:
- **pytest**: Core testing framework for all backend tests
- **pytest-asyncio**: For testing AsyncNode patterns
- **requests**: For API endpoint testing
- **tempfile**: For temporary file creation in tests

**Testing Patterns** [Source: architecture/testing-strategy.md#node-unit-testing]:
- Test each Node's prep/exec/post phases independently
- Test Flow orchestration and Node communication via shared store
- Test API endpoint integration with authentication
- Test file upload scenarios with various file types and sizes

**Specific Testing Requirements**:
- Mock file system operations for unit tests
- Test file validation with invalid file types and oversized files
- Test authentication failure scenarios
- Test Celery job dispatch with queue mocking
- Test database rollback on upload failures
