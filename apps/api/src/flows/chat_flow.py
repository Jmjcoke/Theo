"""
ChatFlow for orchestrating chat operations with intent recognition.

Following PocketFlow AsyncFlow pattern for conditional execution.
Orchestrates: IntentRecognition → [ConditionalRAG] → ResponseGeneration
"""

import logging
import uuid
import time
from typing import Dict, Any
from pocketflow import AsyncFlow

from ..nodes.chat.intent_recognition_node import IntentRecognitionNode
from .basic_rag_flow import BasicRAGFlow
from .advanced_rag_flow import AdvancedRAGFlow
from ..nodes.chat.simple_generator_node import SimpleGeneratorNode
from ..nodes.chat.formatting_node import FormattingNode

logger = logging.getLogger(__name__)


class ChatFlow(AsyncFlow):
    """
    Orchestrates the complete chat pipeline with intent-based routing.
    
    Sequential execution: IntentRecognition → [ConditionalRAG/DirectResponse] → ResponseFormatting
    
    Input: message, context, session_id, user_id, useAdvancedPipeline
    Output: response, confidence, sources, intent, processing metadata
    """
    
    def __init__(self):
        """
        Initialize the chat flow with intent recognition and conditional RAG.
        
        Implements robust dependency initialization with comprehensive error handling
        and graceful fallback mechanisms for improved reliability.
        """
        super().__init__()
        
        # Initialize components with detailed error handling
        initialization_errors = []
        
        try:
            # Initialize intent recognition with error isolation
            logger.info("Initializing IntentRecognitionNode...")
            self.intent_recognition = self._safe_initialize_intent_recognition()
            logger.info("IntentRecognitionNode initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize IntentRecognitionNode: {str(e)}"
            logger.error(error_msg)
            initialization_errors.append(error_msg)
            self.intent_recognition = None
        
        try:
            # Initialize RAG flows with error isolation
            logger.info("Initializing RAG flows...")
            self.basic_rag_flow = self._safe_initialize_basic_rag_flow()
            self.advanced_rag_flow = self._safe_initialize_advanced_rag_flow()
            logger.info("RAG flows initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize RAG flows: {str(e)}"
            logger.error(error_msg)
            initialization_errors.append(error_msg)
            self.basic_rag_flow = None
            self.advanced_rag_flow = None
        
        try:
            # Initialize format generator with error isolation
            logger.info("Initializing SimpleGeneratorNode...")
            self.format_generator = self._safe_initialize_format_generator()
            logger.info("SimpleGeneratorNode initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize SimpleGeneratorNode: {str(e)}"
            logger.error(error_msg)
            initialization_errors.append(error_msg)
            self.format_generator = None
        
        try:
            # Initialize formatting node with error isolation
            logger.info("Initializing FormattingNode...")
            self.formatting_node = self._safe_initialize_formatting_node()
            logger.info("FormattingNode initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize FormattingNode: {str(e)}"
            logger.error(error_msg)
            initialization_errors.append(error_msg)
            self.formatting_node = None
        
        # Check if any critical components failed to initialize
        if initialization_errors:
            combined_error = "ChatFlow initialization failed with errors:\n  - " + "\n  - ".join(initialization_errors)
            logger.error(combined_error)
            raise RuntimeError(combined_error)
        
        try:
            # Validate all dependencies are properly initialized
            logger.info("Validating ChatFlow dependencies...")
            self._validate_dependencies()
            
            # Connect intent recognition as starting point
            self.start(self.intent_recognition)
            
            logger.info("ChatFlow initialization completed successfully")
            
        except Exception as e:
            logger.error(f"ChatFlow post-initialization validation failed: {e}")
            raise RuntimeError(f"ChatFlow initialization failed during validation: {e}")
    
    def _safe_initialize_intent_recognition(self):
        """Safely initialize IntentRecognitionNode with error handling"""
        try:
            from ..nodes.chat.intent_recognition_node import IntentRecognitionNode
            return IntentRecognitionNode(
                model="gpt-4",
                temperature=0.1
            )
        except ImportError as e:
            raise ImportError(f"Cannot import IntentRecognitionNode: {e}")
        except Exception as e:
            raise RuntimeError(f"IntentRecognitionNode initialization failed: {e}")
    
    def _safe_initialize_basic_rag_flow(self):
        """Safely initialize BasicRAGFlow with error handling"""
        try:
            from .basic_rag_flow import BasicRAGFlow
            return BasicRAGFlow()
        except ImportError as e:
            raise ImportError(f"Cannot import BasicRAGFlow: {e}")
        except Exception as e:
            raise RuntimeError(f"BasicRAGFlow initialization failed: {e}")
    
    def _safe_initialize_advanced_rag_flow(self):
        """Safely initialize AdvancedRAGFlow with error handling"""
        try:
            from .advanced_rag_flow import AdvancedRAGFlow
            return AdvancedRAGFlow()
        except ImportError as e:
            raise ImportError(f"Cannot import AdvancedRAGFlow: {e}")
        except Exception as e:
            raise RuntimeError(f"AdvancedRAGFlow initialization failed: {e}")
    
    def _safe_initialize_format_generator(self):
        """Safely initialize SimpleGeneratorNode with error handling"""
        try:
            from ..nodes.chat.simple_generator_node import SimpleGeneratorNode
            return SimpleGeneratorNode(
                model="gpt-4",
                max_tokens=1000,
                temperature=0.3
            )
        except ImportError as e:
            raise ImportError(f"Cannot import SimpleGeneratorNode: {e}")
        except Exception as e:
            raise RuntimeError(f"SimpleGeneratorNode initialization failed: {e}")
    
    def _safe_initialize_formatting_node(self):
        """Safely initialize FormattingNode with error handling"""
        try:
            from ..nodes.chat.formatting_node import FormattingNode
            return FormattingNode(
                model="gpt-4",
                temperature=0.3
            )
        except ImportError as e:
            raise ImportError(f"Cannot import FormattingNode: {e}")
        except Exception as e:
            raise RuntimeError(f"FormattingNode initialization failed: {e}")
    
    def _validate_dependencies(self):
        """
        Validate that all required dependencies are properly initialized.
        
        Performs comprehensive checks including:
        - Component existence
        - Required method availability
        - Component configuration validation
        - Dependency health checks
        """
        validation_errors = []
        
        # Define required components with their expected interfaces
        required_components = {
            'intent_recognition': {
                'instance': self.intent_recognition,
                'required_methods': ['_run_async', 'prep_async', 'exec_async', 'post_async'],
                'expected_type': 'IntentRecognitionNode'
            },
            'basic_rag_flow': {
                'instance': self.basic_rag_flow,
                'required_methods': ['run'],
                'expected_type': 'BasicRAGFlow'
            },
            'advanced_rag_flow': {
                'instance': self.advanced_rag_flow,
                'required_methods': ['run'],
                'expected_type': 'AdvancedRAGFlow'
            },
            'format_generator': {
                'instance': self.format_generator,
                'required_methods': ['_run_async'],
                'expected_type': 'SimpleGeneratorNode'
            },
            'formatting_node': {
                'instance': self.formatting_node,
                'required_methods': ['_run_async', 'prep_async', 'exec_async', 'post_async'],
                'expected_type': 'FormattingNode'
            }
        }
        
        for name, config in required_components.items():
            component = config['instance']
            
            # Check if component exists
            if component is None:
                validation_errors.append(f"Missing component: {name}")
                continue
            
            # Check component type (warning only)
            expected_type = config['expected_type']
            actual_type = type(component).__name__
            if actual_type != expected_type:
                logger.warning(f"Component {name} has unexpected type: {actual_type} (expected: {expected_type})")
            
            # Check required methods
            for method_name in config['required_methods']:
                if not hasattr(component, method_name):
                    validation_errors.append(f"Component {name} missing method: {method_name}")
                elif not callable(getattr(component, method_name)):
                    validation_errors.append(f"Component {name}.{method_name} is not callable")
            
            # Perform component-specific validation
            try:
                self._validate_component_config(name, component)
            except Exception as e:
                validation_errors.append(f"Component {name} configuration error: {str(e)}")
        
        # Report validation results
        if validation_errors:
            error_msg = f"ChatFlow dependency validation failed:\n  - " + "\n  - ".join(validation_errors)
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("ChatFlow dependencies validated successfully - all components ready")
    
    def _validate_component_config(self, name: str, component):
        """Validate individual component configuration"""
        if name == 'intent_recognition':
            # Validate IntentRecognitionNode configuration
            if hasattr(component, 'model') and not component.model:
                raise ValueError("Intent recognition model not configured")
            
        elif name in ['basic_rag_flow', 'advanced_rag_flow']:
            # Validate RAG flow configuration (basic health check)
            # Note: Full validation would require checking internal pipeline components
            pass
            
        elif name == 'format_generator':
            # Validate SimpleGeneratorNode configuration
            if hasattr(component, 'model') and not component.model:
                raise ValueError("Format generator model not configured")
        
        elif name == 'formatting_node':
            # Validate FormattingNode configuration
            if hasattr(component, 'model') and not component.model:
                raise ValueError("Formatting node model not configured")
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare shared store for chat pipeline execution"""
        try:
            # Validate required inputs
            required_fields = ['message', 'session_id', 'user_id']
            for field in required_fields:
                if field not in shared_store:
                    raise ValueError(f"Missing required field: {field}")
            
            # Initialize chat pipeline metadata
            chat_id = str(uuid.uuid4())
            shared_store['chat_id'] = chat_id
            import time
            shared_store['chat_start_time'] = time.time()
            logger.info(f"Chat pipeline started: {chat_id}")
            
            # Set defaults
            if 'context' not in shared_store:
                shared_store['context'] = 'general'
            if 'useAdvancedPipeline' not in shared_store:
                shared_store['useAdvancedPipeline'] = True
            
            # Initialize result containers
            shared_store['chat_errors'] = []
            shared_store['chat_metadata'] = {}
            
            logger.info(f"Chat pipeline initialized for message: {shared_store['message'][:50]}...")
            return shared_store
            
        except Exception as e:
            logger.error(f"ChatFlow prep error: {str(e)}")
            shared_store['chat_error'] = str(e)
            return shared_store
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: str) -> Dict[str, Any]:
        """Process final chat results and format response"""
        try:
            chat_id = shared_store.get('chat_id', 'unknown')
            intent = shared_store.get('intent', 'new_query')
            
            # Calculate total processing time
            start_time = shared_store.get('chat_start_time', 0)
            processing_time = int((time.time() - start_time) * 1000) if start_time else 0
            
            # Check if pipeline completed successfully
            if exec_result == "success" and 'generated_answer' in shared_store:
                # Format response based on intent type
                if intent == 'format_request':
                    # Format request response (no RAG sources)
                    response_data = {
                        "success": True,
                        "response": shared_store.get('generated_answer', ''),
                        "confidence": shared_store.get('confidence', 0.8),
                        "sources": [],  # No sources for formatting requests
                        "intent": intent,
                        "intent_confidence": shared_store.get('intent_confidence', 0.0),
                        "chat_metadata": {
                            "chat_id": chat_id,
                            "intent_model": shared_store.get('intent_model'),
                            "response_model": shared_store.get('generation_model'),
                            "processing_time_ms": processing_time,
                            "pipeline_type": "format_request"
                        }
                    }
                else:
                    # New query response (with RAG sources)
                    sources = []
                    rag_sources = shared_store.get('sources', [])
                    for source in rag_sources:
                        sources.append({
                            "document_id": source.get('document_id'),
                            "title": source.get('title', 'Unknown Document'),
                            "excerpt": source.get('excerpt', ''),
                            "relevance": source.get('relevance', 0.0),
                            "citation": source.get('citation')
                        })
                    
                    response_data = {
                        "success": True,
                        "response": shared_store.get('generated_answer', ''),
                        "confidence": shared_store.get('confidence', 0.0),
                        "sources": sources,
                        "intent": intent,
                        "intent_confidence": shared_store.get('intent_confidence', 0.0),
                        "chat_metadata": {
                            "chat_id": chat_id,
                            "intent_model": shared_store.get('intent_model'),
                            "rag_pipeline_used": shared_store.get('useAdvancedPipeline', False),
                            "processing_time_ms": processing_time,
                            "pipeline_type": "rag_query",
                            "sources_count": len(sources)
                        }
                    }
                    
                    # Add RAG pipeline metadata if available
                    if 'pipeline_metadata' in shared_store:
                        response_data['chat_metadata']['rag_metadata'] = shared_store['pipeline_metadata']
                
                logger.info(f"Chat pipeline completed successfully: {chat_id} (intent: {intent})")
                return response_data
            
            else:
                # Handle pipeline failure
                error_messages = []
                
                # Collect errors from different stages
                if 'intent_error' in shared_store:
                    error_messages.append(f"Intent: {shared_store['intent_error']}")
                
                if 'rag_error' in shared_store:
                    error_messages.append(f"RAG: {shared_store['rag_error']}")
                
                if 'generation_error' in shared_store:
                    error_messages.append(f"Generation: {shared_store['generation_error']}")
                
                if 'formatting_error' in shared_store:
                    error_messages.append(f"Formatting: {shared_store['formatting_error']}")
                
                if 'chat_error' in shared_store:
                    error_messages.append(f"Chat: {shared_store['chat_error']}")
                
                combined_error = "; ".join(error_messages) if error_messages else "Unknown chat pipeline failure"
                
                response_data = {
                    "success": False,
                    "error": combined_error,
                    "intent": shared_store.get('intent', 'unknown'),
                    "chat_metadata": {
                        "chat_id": chat_id,
                        "failure_stage": exec_result if exec_result != "success" else "unknown",
                        "processing_time_ms": processing_time
                    }
                }
                
                logger.error(f"Chat pipeline failed: {chat_id} - {combined_error}")
                return response_data
                
        except Exception as e:
            logger.error(f"ChatFlow post error: {str(e)}")
            processing_time = int((time.time() - shared_store.get('chat_start_time', 0)) * 1000)
            return {
                "success": False,
                "error": f"Chat post-processing failed: {str(e)}",
                "chat_metadata": {
                    "chat_id": shared_store.get('chat_id', 'unknown'),
                    "processing_time_ms": processing_time
                }
            }
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete chat pipeline with intent-based routing"""
        try:
            # First run intent recognition
            intent_result = await self.intent_recognition._run_async(shared_store)
            
            if intent_result != "success":
                shared_store['chat_error'] = "Intent recognition failed"
                return await self.post_async(shared_store, shared_store, "failed")
            
            intent = shared_store.get('intent', 'new_query')
            logger.info(f"Intent recognized: {intent}")
            
            # Route based on intent
            if intent == 'format_request':
                # Handle format request with FormattingNode (skip RAG)
                # Run formatting node
                format_result = await self.formatting_node._run_async(shared_store)
                
                if format_result != "success":
                    shared_store['formatting_error'] = "Formatting operation failed"
                    return await self.post_async(shared_store, shared_store, "failed")
                
                return await self.post_async(shared_store, shared_store, "success")
            
            else:
                # Handle new query with RAG pipeline
                shared_store['query'] = shared_store['message']  # Set query for RAG flow
                
                # Choose RAG pipeline
                use_advanced = shared_store.get('useAdvancedPipeline', True)
                rag_flow = self.advanced_rag_flow if use_advanced else self.basic_rag_flow
                
                # Execute RAG pipeline
                rag_result = await rag_flow.run(shared_store)
                
                if not rag_result.get('success', False):
                    shared_store['rag_error'] = rag_result.get('error', 'RAG pipeline failed')
                    return await self.post_async(shared_store, shared_store, "failed")
                
                # Merge RAG results into shared store
                shared_store['generated_answer'] = rag_result.get('response', '')
                shared_store['confidence'] = rag_result.get('confidence', 0.0)
                shared_store['sources'] = rag_result.get('sources', [])
                shared_store['pipeline_metadata'] = rag_result.get('pipeline_metadata', {})
                
                return await self.post_async(shared_store, shared_store, "success")
            
        except Exception as e:
            logger.error(f"ChatFlow run error: {str(e)}")
            shared_store['chat_error'] = f"Pipeline execution failed: {str(e)}"
            return await self.post_async(shared_store, shared_store, "failed")