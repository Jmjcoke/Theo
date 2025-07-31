"""
Standardized test fixtures and mocking patterns for ChatFlow tests.

This module provides consistent, reusable mocking patterns to improve
test reliability and maintainability across the ChatFlow test suite.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional


class MockIntentRecognitionNode:
    """Standardized mock for IntentRecognitionNode"""
    
    def __init__(self, return_value: str = "success", intent: str = "new_query", confidence: float = 0.9):
        self.return_value = return_value
        self.intent = intent
        self.confidence = confidence
        self._run_async = AsyncMock(return_value=return_value)
        
        # Configure side effect to set intent in shared_store
        async def mock_run_async(shared_store: Dict[str, Any]) -> str:
            if return_value == "success":
                shared_store['intent'] = self.intent
                shared_store['intent_confidence'] = self.confidence
                shared_store['intent_model'] = 'gpt-4'
            return return_value
            
        self._run_async.side_effect = mock_run_async


class MockRAGFlow:
    """Standardized mock for RAG flows (Basic and Advanced)"""
    
    def __init__(self, success: bool = True, response: str = "Test response", 
                 confidence: float = 0.85, sources: Optional[list] = None,
                 error: Optional[str] = None):
        self.success = success
        self.response = response
        self.confidence = confidence
        self.sources = sources or []
        self.error = error
        
        result = {
            'success': success,
            'response': response,
            'confidence': confidence,
            'sources': sources or [],
            'pipeline_metadata': {
                'pipeline_id': 'test-pipeline-123',
                'embedding_model': 'text-embedding-ada-002',
                'generation_model': 'gpt-4'
            }
        }
        
        if not success and error:
            result['error'] = error
            
        self.run = AsyncMock(return_value=result)


class MockSimpleGeneratorNode:
    """Standardized mock for SimpleGeneratorNode"""
    
    def __init__(self, return_value: str = "success", response: str = "Formatted response",
                 confidence: float = 0.8):
        self.return_value = return_value
        self.response = response
        self.confidence = confidence
        self._run_async = AsyncMock(return_value=return_value)
        
        # Configure side effect to set response in shared_store
        async def mock_run_async(shared_store: Dict[str, Any]) -> str:
            if return_value == "success":
                shared_store['generated_answer'] = self.response
                shared_store['confidence'] = self.confidence
                shared_store['generation_model'] = 'gpt-4'
            return return_value
            
        self._run_async.side_effect = mock_run_async


class MockFormattingNode:
    """Standardized mock for FormattingNode"""
    
    def __init__(self, return_value: str = "success", response: str = "• Formatted bullet points",
                 confidence: float = 0.9):
        self.return_value = return_value
        self.response = response
        self.confidence = confidence
        self._run_async = AsyncMock(return_value=return_value)
        
        # Configure side effect to set formatting response in shared_store
        async def mock_run_async(shared_store: Dict[str, Any]) -> str:
            if return_value == "success":
                shared_store['generated_answer'] = self.response
                shared_store['confidence'] = self.confidence
                shared_store['generation_model'] = 'gpt-4'
                shared_store['formatting_applied'] = 'bullet_points'
                shared_store['original_text'] = shared_store.get('previous_response', 'Original text')
            elif return_value == "error":
                shared_store['formatting_error'] = "Formatting operation failed"
            return return_value
            
        self._run_async.side_effect = mock_run_async


@pytest.fixture
def mock_intent_node_success():
    """Fixture for successful intent recognition (new_query)"""
    return MockIntentRecognitionNode(
        return_value="success",
        intent="new_query",
        confidence=0.9
    )


@pytest.fixture
def mock_intent_node_format_request():
    """Fixture for successful intent recognition (format_request)"""
    return MockIntentRecognitionNode(
        return_value="success",
        intent="format_request",
        confidence=0.92
    )


@pytest.fixture
def mock_intent_node_failure():
    """Fixture for failed intent recognition"""
    return MockIntentRecognitionNode(
        return_value="failed",
        intent="unknown",
        confidence=0.0
    )


@pytest.fixture
def mock_basic_rag_flow_success():
    """Fixture for successful basic RAG flow"""
    sources = [
        {
            'document_id': '123',
            'title': 'Test Document',
            'excerpt': 'Test excerpt content',
            'relevance': 0.88,
            'citation': 'Test Citation'
        }
    ]
    return MockRAGFlow(
        success=True,
        response="Basic RAG response about biblical topics.",
        confidence=0.88,
        sources=sources
    )


@pytest.fixture
def mock_advanced_rag_flow_success():
    """Fixture for successful advanced RAG flow"""
    sources = [
        {
            'document_id': '123',
            'title': 'Genesis Commentary',
            'excerpt': 'In the beginning God created the heavens and the earth...',
            'relevance': 0.95,
            'citation': 'Genesis 1:1'
        },
        {
            'document_id': '456',
            'title': 'Creation Theology',
            'excerpt': 'The doctrine of creation establishes fundamental truths...',
            'relevance': 0.87,
            'citation': 'Genesis 1:1-3'
        }
    ]
    return MockRAGFlow(
        success=True,
        response="Genesis 1:1 establishes God as the ultimate creator of all things.",
        confidence=0.95,
        sources=sources
    )


@pytest.fixture
def mock_rag_flow_failure():
    """Fixture for failed RAG flow"""
    return MockRAGFlow(
        success=False,
        response="",
        confidence=0.0,
        sources=[],
        error="Embedding service unavailable"
    )


@pytest.fixture
def mock_format_generator_success():
    """Fixture for successful format generator"""
    return MockSimpleGeneratorNode(
        return_value="success",
        response="• Point 1: Formatted content\n• Point 2: More formatted content\n• Point 3: Additional points",
        confidence=0.8
    )


@pytest.fixture
def mock_format_generator_failure():
    """Fixture for failed format generator"""
    return MockSimpleGeneratorNode(
        return_value="failed",
        response="",
        confidence=0.0
    )


class ChatFlowTestHelper:
    """Helper class for ChatFlow testing with standardized patterns"""
    
    @staticmethod
    def setup_flow_mocks(flow, intent_mock=None, rag_mock=None, format_mock=None, formatting_mock=None):
        """Apply standardized mocks to a ChatFlow instance"""
        if intent_mock:
            flow.intent_recognition = intent_mock
            
        if rag_mock:
            # Apply to both basic and advanced flows
            flow.basic_rag_flow = rag_mock
            flow.advanced_rag_flow = rag_mock
            
        if format_mock:
            flow.format_generator = format_mock
            
        if formatting_mock:
            flow.formatting_node = formatting_mock
    
    @staticmethod
    def create_valid_shared_store(intent_type: str = "new_query", 
                                  use_advanced: bool = True) -> Dict[str, Any]:
        """Create a properly structured shared store for testing"""
        base_store = {
            'message': 'What does Genesis 1:1 teach us about creation?',
            'session_id': 'test-session-123',
            'user_id': 'test-user-456',
            'context': 'biblical-exegesis',
            'useAdvancedPipeline': use_advanced
        }
        
        if intent_type == "format_request":
            base_store['message'] = 'Format the previous response as bullet points'
            base_store['context'] = 'general'
            base_store['useAdvancedPipeline'] = False
            base_store['previous_response'] = 'Genesis 1:1 establishes that God is the creator of all things.'
            
        return base_store
    
    @staticmethod
    def validate_success_response(result: Dict[str, Any], intent: str, 
                                  expected_sources_count: int = 0):
        """Validate structure of successful ChatFlow response"""
        assert result['success'] is True
        assert result['intent'] == intent
        assert 'response' in result
        assert 'confidence' in result
        assert 'sources' in result
        assert len(result['sources']) == expected_sources_count
        assert 'chat_metadata' in result
        assert 'processing_time_ms' in result['chat_metadata']
        assert 'pipeline_type' in result['chat_metadata']
        
        if intent == 'format_request':
            assert result['chat_metadata']['pipeline_type'] == 'format_request'
            assert 'rag_metadata' not in result['chat_metadata']
        else:
            assert result['chat_metadata']['pipeline_type'] == 'rag_query'
            assert 'sources_count' in result['chat_metadata']
    
    @staticmethod
    def validate_failure_response(result: Dict[str, Any], expected_error_substring: str = None):
        """Validate structure of failed ChatFlow response"""
        assert result['success'] is False
        assert 'error' in result
        assert 'chat_metadata' in result
        assert 'processing_time_ms' in result['chat_metadata']
        
        if expected_error_substring:
            assert expected_error_substring in result['error']


@pytest.fixture
def chat_flow_helper():
    """Fixture providing ChatFlow test helper utilities"""
    return ChatFlowTestHelper()