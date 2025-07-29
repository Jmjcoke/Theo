"""
BasicRAGFlow for orchestrating RAG pipeline operations.

Following PocketFlow AsyncFlow pattern for sequential Node execution.
Orchestrates: QueryEmbedder → SupabaseSearch → SimpleGenerator
"""

import logging
import uuid
from typing import Dict, Any
from pocketflow import AsyncFlow

from ..nodes.chat.query_embedder_node import QueryEmbedderNode
from ..nodes.chat.supabase_search_node import SupabaseSearchNode
from ..nodes.chat.re_ranker_node import ReRankerNode
from ..nodes.chat.simple_generator_node import SimpleGeneratorNode

logger = logging.getLogger(__name__)


class BasicRAGFlow(AsyncFlow):
    """
    Orchestrates the complete RAG pipeline for question answering.
    
    Sequential execution: QueryEmbedder → SupabaseSearch → ReRanker → SimpleGenerator
    
    Input: query, context, session_id, user_id
    Output: response, confidence, sources, processing metadata
    """
    
    def __init__(self):
        """Initialize the RAG flow with connected nodes"""
        super().__init__()
        
        # Initialize nodes
        self.query_embedder = QueryEmbedderNode()
        self.supabase_search = SupabaseSearchNode(
            similarity_threshold=0.7,
            result_limit=10  # Increased to allow re-ranking to select top 5
        )
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
        
        # Connect nodes in sequence: QueryEmbedder → SupabaseSearch → ReRanker → SimpleGenerator
        self.start(self.query_embedder)
        self.query_embedder >> self.supabase_search
        self.supabase_search >> self.re_ranker
        self.re_ranker >> self.simple_generator
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare shared store for RAG pipeline execution"""
        try:
            # Validate required inputs
            required_fields = ['query', 'session_id', 'user_id']
            for field in required_fields:
                if field not in shared_store:
                    raise ValueError(f"Missing required field: {field}")
            
            # Initialize pipeline metadata
            pipeline_id = str(uuid.uuid4())
            shared_store['pipeline_id'] = pipeline_id
            import time
            shared_store['pipeline_start_time'] = time.time()
            logger.info(f"RAG pipeline started: {pipeline_id}")
            
            # Set default context if not provided
            if 'context' not in shared_store:
                shared_store['context'] = 'general'
            
            # Initialize result containers
            shared_store['pipeline_errors'] = []
            shared_store['node_results'] = {}
            
            logger.info(f"RAG pipeline initialized for query: {shared_store['query'][:50]}...")
            return shared_store
            
        except Exception as e:
            logger.error(f"BasicRAGFlow prep error: {str(e)}")
            shared_store['pipeline_error'] = str(e)
            return shared_store
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: str) -> Dict[str, Any]:
        """Process final results and format response"""
        try:
            pipeline_id = shared_store.get('pipeline_id', 'unknown')
            
            # Check if pipeline completed successfully
            if exec_result == "success" and 'generated_answer' in shared_store:
                # Format successful response using re-ranked results if available
                source_results = shared_store.get('re_ranked_results', shared_store.get('search_results', []))
                sources = []
                for result in source_results:
                    sources.append({
                        "document_id": result.get('document_id'),
                        "title": result.get('title', 'Unknown Document'),
                        "excerpt": result.get('excerpt', ''),
                        "relevance": result.get('llm_relevance', result.get('relevance', 0.0)),
                        "original_relevance": result.get('relevance', 0.0),
                        "citation": result.get('citation'),
                        "re_ranking_reasoning": result.get('re_ranking_reasoning', '')
                    })
                
                response_data = {
                    "success": True,
                    "response": shared_store.get('generated_answer', ''),
                    "confidence": shared_store.get('confidence', 0.0),
                    "sources": sources,
                    "pipeline_metadata": {
                        "pipeline_id": pipeline_id,
                        "embedding_model": shared_store.get('embedding_model'),
                        "generation_model": shared_store.get('generation_model'),
                        "re_ranking_metadata": shared_store.get('re_ranking_metadata', {}),
                        "context_sources_count": shared_store.get('context_sources_count', 0),
                        "search_result_count": shared_store.get('result_count', 0),
                        "re_ranked_count": len(source_results)
                    }
                }
                
                logger.info(f"RAG pipeline completed successfully: {pipeline_id}")
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
                
                logger.error(f"RAG pipeline failed: {pipeline_id} - {combined_error}")
                return response_data
                
        except Exception as e:
            logger.error(f"BasicRAGFlow post error: {str(e)}")
            return {
                "success": False,
                "error": f"Pipeline post-processing failed: {str(e)}",
                "pipeline_metadata": {
                    "pipeline_id": shared_store.get('pipeline_id', 'unknown')
                }
            }
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete RAG pipeline"""
        try:
            # Use AsyncFlow's run_async method for proper execution
            await self.run_async(shared_store)
            
            # Return the processed results from post_async
            return shared_store.get('final_result', {
                "success": False,
                "error": "Pipeline execution failed"
            })
            
        except Exception as e:
            logger.error(f"BasicRAGFlow run error: {str(e)}")
            return {
                "success": False,
                "error": f"Pipeline execution failed: {str(e)}"
            }
    
    async def _run_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Override to store final result in shared store"""
        result = await super()._run_async(shared_store)
        shared_store['final_result'] = result
        return result