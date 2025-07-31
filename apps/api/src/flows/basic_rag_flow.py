"""
BasicRAGFlow for orchestrating RAG pipeline operations.

Following PocketFlow AsyncFlow pattern with performance optimizations.
Orchestrates: QueryEmbedder → SupabaseSearch → SimpleGenerator
Enhanced with: timeout management, circuit breakers, caching, parallel processing
"""

import logging
import uuid
import asyncio
from typing import Dict, Any
from pocketflow import AsyncFlow

from ..nodes.chat.supabase_edge_search_node import SupabaseEdgeSearchNode
from ..nodes.chat.re_ranker_node import ReRankerNode
from ..nodes.chat.simple_generator_node import SimpleGeneratorNode
from ..utils.performance_utils import (
    TimeoutManager, 
    get_performance_cache,
    get_performance_metrics,
    with_performance_monitoring,
    with_circuit_breaker
)

logger = logging.getLogger(__name__)


class BasicRAGFlow(AsyncFlow):
    """
    Orchestrates the complete RAG pipeline for question answering.
    
    Sequential execution: EdgeSearch → ReRanker → SimpleGenerator
    Note: Query embedding now handled by Edge Function
    
    Input: query, context, session_id, user_id
    Output: response, confidence, sources, processing metadata
    """
    
    def __init__(self):
        """Initialize the RAG flow with connected nodes"""
        # Initialize nodes - Edge Function handles query embedding
        self.edge_search = SupabaseEdgeSearchNode(result_limit=10)
        self.re_ranker = ReRankerNode(
            model="gpt-4",
            top_k=5,
            temperature=0.1
        )
        self.simple_generator = SimpleGeneratorNode(
            model="gpt-4",
            max_tokens=1000,
            temperature=0.7
        )
        
        # Connect nodes in sequence: EdgeSearch → ReRanker → SimpleGenerator
        self.edge_search >> self.re_ranker
        self.re_ranker >> self.simple_generator
        
        # Initialize AsyncFlow with proper start node
        super().__init__(start=self.edge_search)
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> bool:
        """Prepare shared store for RAG pipeline execution with performance optimizations"""
        pipeline_id = str(uuid.uuid4())
        shared_store['pipeline_id'] = pipeline_id
        
        # Start performance tracking
        metrics = get_performance_metrics()
        metrics.start_operation(pipeline_id, 'basic_rag_pipeline')
        
        try:
            # Validate required inputs
            required_fields = ['query', 'session_id', 'user_id']
            for field in required_fields:
                if field not in shared_store:
                    raise ValueError(f"Missing required field: {field}")
            
            # Initialize pipeline metadata with performance tracking
            import time
            shared_store['pipeline_start_time'] = time.time()
            shared_store['pipeline_type'] = 'basic_rag'
            logger.info(f"Basic RAG pipeline started: {pipeline_id}")
            
            # Set default context if not provided
            if 'context' not in shared_store:
                shared_store['context'] = 'general'
            
            # Initialize result containers
            shared_store['pipeline_errors'] = []
            shared_store['node_results'] = {}
            shared_store['performance_metadata'] = {
                'pipeline_id': pipeline_id,
                'cache_enabled': True,
                'timeout_settings': {
                    'edge_function': TimeoutManager.get_timeout('edge_function'),
                    'llm_request': TimeoutManager.get_timeout('llm_request'),
                    'total_pipeline': TimeoutManager.get_timeout('rag_pipeline')
                }
            }
            
            # Check cache for similar queries
            cache = get_performance_cache()
            query = shared_store['query']
            cache_key = cache.generate_key('basic_rag', query=query, context=shared_store.get('context', 'general'))
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Cache hit for basic RAG query: {query[:50]}...")
                shared_store['cached_result'] = cached_result
                shared_store['cache_key'] = cache_key
                shared_store['cache_hit'] = True
            else:
                shared_store['cache_key'] = cache_key
                shared_store['cache_hit'] = False
            
            logger.info(f"Basic RAG pipeline initialized for query: {query[:50]}... (cached: {shared_store['cache_hit']})")
            return True
            
        except Exception as e:
            logger.error(f"BasicRAGFlow prep error: {str(e)}")
            shared_store['pipeline_error'] = str(e)
            
            # Record failure in metrics
            metrics.end_operation(pipeline_id, success=False, error=str(e))
            return False
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: bool, exec_result: str) -> Dict[str, Any]:
        """Process final results and format response with performance optimizations"""
        pipeline_id = shared_store.get('pipeline_id', 'unknown')
        metrics = get_performance_metrics()
        
        try:
            # Check if we used cached result
            if shared_store.get('cache_hit', False):
                cached_result = shared_store.get('cached_result')
                if cached_result:
                    logger.info(f"Returning cached result for pipeline: {pipeline_id}")
                    metrics.end_operation(pipeline_id, success=True)
                    shared_store['final_result'] = cached_result
                    return cached_result
            
            # Check if pipeline completed successfully
            if exec_result == "success" and 'generated_answer' in shared_store:
                # Format successful response using re-ranked results if available
                source_results = shared_store.get('re_ranked_results', shared_store.get('search_results', []))
                sources = []
                for result in source_results:
                    sources.append({
                        "document_id": result.get('document_id'),
                        "title": result.get('title', result.get('document_title', 'Unknown Document')),
                        "excerpt": result.get('excerpt', ''),
                        "relevance": result.get('llm_relevance', result.get('relevance', 0.0)),
                        "original_relevance": result.get('relevance', 0.0),
                        "citation": result.get('citation'),
                        "re_ranking_reasoning": result.get('re_ranking_reasoning', ''),
                        "document_type": result.get('document_type', 'unknown'),
                        "approximate_page": result.get('approximate_page', 1),
                        "paragraph_indicator": result.get('paragraph_indicator', 'Section 1'),
                        "chunk_index": result.get('chunk_index', 0)
                    })
                
                # Calculate performance metrics
                pipeline_end_time = shared_store.get('pipeline_start_time', 0)
                import time
                total_time = time.time() - pipeline_end_time if pipeline_end_time else 0
                
                response_data = {
                    "success": True,
                    "response": shared_store.get('generated_answer', ''),
                    "confidence": shared_store.get('confidence', 0.0),
                    "sources": sources,
                    "pipeline_metadata": {
                        "pipeline_id": pipeline_id,
                        "pipeline_type": "basic_rag",
                        "embedding_model": shared_store.get('embedding_model'),
                        "generation_model": shared_store.get('generation_model'),
                        "re_ranking_metadata": shared_store.get('re_ranking_metadata', {}),
                        "context_sources_count": shared_store.get('context_sources_count', 0),
                        "search_result_count": shared_store.get('result_count', 0),
                        "re_ranked_count": len(source_results),
                        "total_pipeline_time_seconds": total_time,
                        "cache_used": False,
                        "performance_metadata": shared_store.get('performance_metadata', {})
                    }
                }
                
                # Cache successful result
                cache = get_performance_cache()
                cache_key = shared_store.get('cache_key')
                if cache_key:
                    cache.set(cache_key, response_data)
                    logger.debug(f"Result cached for future queries: {cache_key}")
                
                logger.info(f"Basic RAG pipeline completed successfully: {pipeline_id} in {total_time:.3f}s")
                metrics.end_operation(pipeline_id, success=True)
                
                # Store final result in shared store for run() method
                shared_store['final_result'] = response_data
                return response_data
            
            else:
                # Handle pipeline failure
                error_messages = []
                
                # Collect errors from different stages
                if 'embedding_error' in shared_store:
                    error_messages.append(f"Embedding: {shared_store['embedding_error']}")
                
                if 'search_error' in shared_store:
                    error_messages.append(f"Search: {shared_store['search_error']}")
                
                if 're_ranking_error' in shared_store:
                    error_messages.append(f"Re-ranking: {shared_store['re_ranking_error']}")
                
                if 'generation_error' in shared_store:
                    error_messages.append(f"Generation: {shared_store['generation_error']}")
                
                if 'pipeline_error' in shared_store:
                    error_messages.append(f"Pipeline: {shared_store['pipeline_error']}")
                
                combined_error = "; ".join(error_messages) if error_messages else "Unknown pipeline failure"
                
                response_data = {
                    "success": False,
                    "error": combined_error,
                    "pipeline_metadata": {
                        "pipeline_id": pipeline_id,
                        "failure_stage": exec_result if exec_result != "success" else "unknown"
                    }
                }
                
                logger.error(f"Basic RAG pipeline failed: {pipeline_id} - {combined_error}")
                metrics.end_operation(pipeline_id, success=False, error=combined_error)
                
                # Store final result in shared store for run() method
                shared_store['final_result'] = response_data
                return response_data
                
        except Exception as e:
            logger.error(f"BasicRAGFlow post error: {str(e)}")
            metrics.end_operation(pipeline_id, success=False, error=str(e))
            
            error_response = {
                "success": False,
                "error": f"Pipeline post-processing failed: {str(e)}",
                "pipeline_metadata": {
                    "pipeline_id": pipeline_id,
                    "pipeline_type": "basic_rag"
                }
            }
            # Store final result in shared store for run() method
            shared_store['final_result'] = error_response
            return error_response
    
    @with_performance_monitoring('basic_rag_execution')
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete RAG pipeline with timeout management"""
        try:
            # Execute with timeout management
            pipeline_execution = self.run_async(shared_store)
            await TimeoutManager.with_timeout(pipeline_execution, 'rag_pipeline')
            
            # Return the processed results from post_async
            result = shared_store.get('final_result', {
                "success": False,
                "error": "RAG pipeline execution failed"
            })
            
            logger.info(f"Basic RAG pipeline run completed: success={result.get('success', False)}")
            return result
            
        except asyncio.TimeoutError:
            error_msg = "Basic RAG pipeline execution timed out"
            logger.error(error_msg)
            
            # Record timeout in metrics if pipeline_id available
            pipeline_id = shared_store.get('pipeline_id')
            if pipeline_id:
                metrics = get_performance_metrics()
                metrics.end_operation(pipeline_id, success=False, error=error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "pipeline_metadata": {
                    "pipeline_type": "basic_rag",
                    "failure_reason": "timeout"
                }
            }
            
        except Exception as e:
            error_msg = f"Basic RAG pipeline execution failed: {str(e)}"
            logger.error(error_msg)
            
            # Record error in metrics if pipeline_id available
            pipeline_id = shared_store.get('pipeline_id')
            if pipeline_id:
                metrics = get_performance_metrics()
                metrics.end_operation(pipeline_id, success=False, error=str(e))
            
            return {
                "success": False,
                "error": error_msg,
                "pipeline_metadata": {
                    "pipeline_type": "basic_rag"
                }
            }