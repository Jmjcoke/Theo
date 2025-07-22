# Testing Strategy

## Overview

Theo's testing strategy is built around PocketFlow's Node/Flow architecture patterns, ensuring that each 150-line Node can be tested independently and Flow compositions can be validated as complete workflows.

## Testing Levels

### 1. Node Unit Testing

**Purpose**: Validate individual PocketFlow Nodes (≤150 lines each) in isolation.

**Testing Pattern**: prep/exec/post Phase Testing
```python
# Example Node test structure
def test_authentication_node():
    # Test prep phase
    node = AuthenticationNode()
    prep_result = node.prep(input_data)
    assert prep_result.status == "ready"
    
    # Test exec phase  
    exec_result = node.exec(prep_result.data)
    assert exec_result.authenticated == True
    
    # Test post phase
    post_result = node.post(exec_result)
    assert post_result.token is not None
```

**Node Test Locations**:
- `apps/api/tests/nodes/` - Backend Node tests
- `apps/workers/tests/nodes/` - Background processing Node tests

**Required Node Test Coverage**:
- ✅ Each Node's prep/exec/post phases tested independently
- ✅ Error handling and retry mechanisms validated
- ✅ Shared store communication patterns tested
- ✅ Async Node timing and concurrency tested
- ✅ 150-line limit compliance validated

### 2. Flow Integration Testing

**Purpose**: Validate PocketFlow Flow compositions and Node orchestration.

**Testing Pattern**: End-to-End Flow Execution
```python
# Example Flow test structure
def test_document_processing_flow():
    # Setup shared store
    shared_store = create_test_store()
    
    # Create and execute flow
    flow = DocumentProcessingFlow(shared_store)
    result = await flow.run(test_document)
    
    # Validate flow completion
    assert result.status == "completed"
    assert result.processed_content is not None
    assert shared_store.get("document_id") is not None
```

**Flow Test Locations**:
- `apps/api/tests/flows/` - Application Flow tests
- `apps/workers/tests/flows/` - Background Flow tests

**Required Flow Test Coverage**:
- ✅ Complete Flow execution from start to finish
- ✅ Node-to-Node data passing via shared store
- ✅ Flow error handling and graceful failures
- ✅ Async Flow timing and coordination
- ✅ Flow retry and recovery mechanisms

### 3. API Integration Testing

**Purpose**: Validate FastAPI endpoints that trigger PocketFlow workflows.

**Testing Pattern**: API-to-Flow Integration
```python
# Example API integration test
def test_chat_endpoint_flow():
    # Test API endpoint
    response = client.post("/api/chat", json=test_message)
    assert response.status_code == 200
    
    # Validate Flow was triggered
    flow_id = response.json()["flow_id"]
    assert flow_id is not None
    
    # Wait for Flow completion (or use WebSocket)
    result = await wait_for_flow_completion(flow_id)
    assert result.status == "completed"
```

**API Test Locations**:
- `apps/api/tests/api/` - FastAPI endpoint tests
- `apps/api/tests/integration/` - Full API-to-Flow tests

### 4. End-to-End Testing

**Purpose**: Validate complete user workflows across frontend and backend.

**Testing Pattern**: User Journey Validation
- User authentication → Auth Flow → JWT token
- Document upload → Document Processing Flow → Analysis results
- Chat interaction → Chat Flow → Real-time responses
- Background job → Async Flow → Completion notification

**E2E Test Locations**:
- `apps/web/tests/e2e/` - Frontend E2E tests
- `tests/e2e/` - Cross-application E2E tests

## Testing Frameworks and Tools

### Backend Testing Stack

**Core Framework**: pytest with PocketFlow extensions
```txt
# Testing dependencies in apps/api/requirements.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0  # For AsyncNode testing
pytest-mock>=3.10.0     # For Node mocking
requests>=2.32.3        # For API testing
```

**PocketFlow-Specific Testing Utilities**:
```python
# utils/testing.py - Custom testing utilities
def create_test_shared_store():
    """Create isolated shared store for testing"""
    
def mock_node_dependencies():
    """Mock external dependencies for Node testing"""
    
def validate_node_size_limit(node_file_path):
    """Ensure Node doesn't exceed 150 lines"""
    
async def run_flow_with_timeout(flow, timeout=30):
    """Execute Flow with timeout for testing"""
```

### Frontend Testing Stack

**Core Framework**: Jest with React Testing Library
```json
// apps/web/package.json testing dependencies
{
  "jest": "^29.0.0",
  "@testing-library/react": "^13.0.0",
  "@testing-library/jest-dom": "^5.16.0",
  "@testing-library/user-event": "^14.0.0"
}
```

## Test Data Management

### Test Data Strategy
- **Isolated Test Database**: SQLite in-memory for unit/integration tests
- **Mock External APIs**: Mock OpenAI, Anthropic, and other external services
- **Test Fixtures**: Reusable test data for consistent testing
- **Shared Store Mocking**: Mock shared store for Node isolation

### Test Data Locations
- `tests/fixtures/` - Reusable test data
- `tests/mocks/` - Mock implementations
- `tests/data/` - Test-specific data files

## PocketFlow Pattern Testing Requirements

### Agent Pattern Testing
```python
# Test agent decision-making workflow
def test_theological_agent_pattern():
    agent_flow = TheologicalAgentFlow()
    result = await agent_flow.run(theological_question)
    
    # Validate agent reasoning
    assert result.reasoning_steps is not None
    assert result.biblical_references is not None
    assert result.confidence_score >= 0.7
```

### RAG Pattern Testing  
```python
# Test retrieval-augmented generation
def test_document_rag_pattern():
    rag_flow = DocumentRAGFlow()
    result = await rag_flow.run(user_query)
    
    # Validate retrieval and generation
    assert result.retrieved_documents is not None
    assert result.generated_response is not None
    assert result.relevance_score >= 0.8
```

### Workflow Pattern Testing
```python
# Test complex workflow orchestration
def test_hermeneutic_workflow_pattern():
    workflow = HermeneuticWorkflow()
    result = await workflow.run(biblical_passage)
    
    # Validate workflow steps
    assert result.linguistic_analysis is not None
    assert result.historical_context is not None
    assert result.theological_implications is not None
```

## Continuous Integration Testing

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: PocketFlow Testing
on: [push, pull_request]

jobs:
  test-nodes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      - name: Install PocketFlow
        run: pip install -e ./PocketFlow-main
      - name: Install dependencies  
        run: pip install -r apps/api/requirements.txt
      - name: Run Node tests
        run: pytest apps/api/tests/nodes/
      - name: Run Flow tests
        run: pytest apps/api/tests/flows/
      - name: Validate Node size limits
        run: python scripts/validate_node_sizes.py
```

## Testing Quality Gates

### Required Before Story Completion
- ✅ All new Nodes have unit tests with >90% coverage
- ✅ All new Flows have integration tests
- ✅ All Nodes respect 150-line limit
- ✅ All async patterns properly tested
- ✅ No test failures in CI pipeline

### Required Before Epic Completion
- ✅ End-to-end user journeys tested
- ✅ Performance testing for Flow execution times
- ✅ Load testing for concurrent Flow execution
- ✅ Security testing for authentication Flows

## Test Execution Commands

### Local Development Testing
```bash
# Run all Node unit tests
cd apps/api && pytest tests/nodes/ -v

# Run all Flow integration tests  
cd apps/api && pytest tests/flows/ -v

# Run API integration tests
cd apps/api && pytest tests/api/ -v

# Run frontend tests
cd apps/web && npm test

# Run E2E tests
cd tests/e2e && npm run test:e2e
```

### Automated Testing
```bash
# Run complete test suite
make test-all

# Run PocketFlow compliance checks
make test-pocketflow-compliance

# Run performance tests
make test-performance
```

## Mock Strategy for External Dependencies

### LLM API Mocking
```python
# Mock OpenAI for consistent testing
@pytest.fixture
def mock_openai():
    with patch('openai.ChatCompletion.create') as mock:
        mock.return_value = create_test_response()
        yield mock
```

### Vector Database Mocking
```python
# Mock vector operations for testing
@pytest.fixture  
def mock_vector_store():
    with patch('utils.vector_utils.VectorStore') as mock:
        mock.return_value = create_test_vector_store()
        yield mock
```

This testing strategy ensures that every PocketFlow Node and Flow is thoroughly tested, maintains the 150-line limit, and follows proven patterns from the PocketFlow cookbook while providing comprehensive coverage for Theo's theological AI assistant functionality.