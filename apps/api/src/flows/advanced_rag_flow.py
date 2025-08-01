"""
AdvancedRAGFlow for orchestrating enhanced RAG pipeline operations.

Following PocketFlow AsyncFlow pattern for sequential Node execution.
Orchestrates: QueryEmbedder → SupabaseSearch → ReRanker → AdvancedGenerator
"""

import logging
import uuid
import time
from typing import Dict, Any
from pocketflow import AsyncFlow

from ..nodes.chat.query_embedder_node import QueryEmbedderNode
from ..nodes.chat.supabase_edge_search_node_deprecated import SupabaseEdgeSearchNode
from ..nodes.chat.compact_re_ranker_node import CompactReRankerNode
from ..nodes.chat.advanced_generator_node import AdvancedGeneratorNode

logger = logging.getLogger(__name__)


class AdvancedRAGFlow(AsyncFlow):
    """
    Orchestrates the enhanced RAG pipeline with re-ranking and hermeneutics filtering.
    
    Sequential execution: QueryEmbedder → SupabaseSearch → ReRanker → AdvancedGenerator
    
    Input: query, context, session_id, user_id
    Output: response, confidence, sources, hermeneutics metadata, performance metrics
    """
    
    def __init__(self):
        """Initialize the advanced RAG flow with individual nodes"""
        # Initialize nodes without AsyncFlow chaining to avoid unhashable dict error
        self.query_embedder = QueryEmbedderNode()
        self.supabase_search = SupabaseEdgeSearchNode(
            result_limit=10  # Increased to allow re-ranking to select top 5
        )
        self.re_ranker = CompactReRankerNode(
            model="gpt-4",
            top_k=5,
            temperature=0.1
        )
        self.advanced_generator = AdvancedGeneratorNode(
            model="gpt-4",
            max_tokens=1500,
            temperature=0.3
        )
        
        # Don't use AsyncFlow node chaining - execute manually to avoid dict hash errors
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare shared store for advanced RAG pipeline execution"""
        try:
            # Validate required inputs
            required_fields = ['query', 'session_id', 'user_id']
            for field in required_fields:
                if field not in shared_store:
                    raise ValueError(f"Missing required field: {field}")
            
            # Initialize pipeline metadata
            pipeline_id = str(uuid.uuid4())
            shared_store['pipeline_id'] = pipeline_id
            shared_store['pipeline_start_time'] = time.time()
            logger.info(f"Advanced RAG pipeline started: {pipeline_id}")
            
            # Set default context if not provided
            if 'context' not in shared_store:
                shared_store['context'] = 'general'
            
            # Initialize result containers
            shared_store['pipeline_errors'] = []
            shared_store['node_results'] = {}
            shared_store['advanced_pipeline_metadata'] = {
                'reranking_enabled': True,
                'hermeneutics_enabled': True,
                'pipeline_type': 'advanced_rag'
            }
            
            logger.info(f"Advanced RAG pipeline initialized for query: {shared_store['query'][:50]}...")
            return shared_store
            
        except Exception as e:
            logger.error(f"AdvancedRAGFlow prep error: {str(e)}")
            shared_store['pipeline_error'] = str(e)
            return shared_store
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: str) -> Dict[str, Any]:
        """Process final results and format advanced response"""
        try:
            pipeline_id = shared_store.get('pipeline_id', 'unknown')
            
            # Check if pipeline completed successfully
            if exec_result == "success" and 'generated_answer' in shared_store:
                # Format successful response using re-ranked results and hermeneutics metadata
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
                
                # Calculate pipeline timing
                pipeline_end_time = time.time()
                pipeline_start_time = shared_store.get('pipeline_start_time', pipeline_end_time)
                total_pipeline_time = pipeline_end_time - pipeline_start_time
                
                response_data = {
                    "success": True,
                    "response": shared_store.get('generated_answer', ''),
                    "confidence": shared_store.get('confidence', 0.0),
                    "sources": sources,
                    "pipeline_metadata": {
                        "pipeline_id": pipeline_id,
                        "pipeline_type": "advanced_rag",
                        "embedding_model": shared_store.get('embedding_model'),
                        "generation_model": shared_store.get('generation_model'),
                        "re_ranking_metadata": shared_store.get('re_ranking_metadata', {}),
                        "hermeneutics_metadata": shared_store.get('hermeneutics_metadata', {}),
                        "context_sources_count": shared_store.get('context_sources_count', 0),
                        "search_result_count": shared_store.get('result_count', 0),
                        "re_ranked_count": len(source_results),
                        "total_pipeline_time": total_pipeline_time,
                        "reranking_applied": 're_ranked_results' in shared_store,
                        "hermeneutics_applied": shared_store.get('hermeneutics_metadata', {}).get('hermeneutics_applied', False)
                    }
                }
                
                logger.info(f"Advanced RAG pipeline completed successfully: {pipeline_id} in {total_pipeline_time:.2f}s")
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
                
                combined_error = "; ".join(error_messages) if error_messages else "Unknown advanced pipeline failure"
                
                response_data = {
                    "success": False,
                    "error": combined_error,
                    "pipeline_metadata": {
                        "pipeline_id": pipeline_id,
                        "pipeline_type": "advanced_rag",
                        "failure_stage": exec_result if exec_result != "success" else "unknown"
                    }
                }
                
                logger.error(f"Advanced RAG pipeline failed: {pipeline_id} - {combined_error}")
                # Store final result in shared store for run() method
                shared_store['final_result'] = response_data
                return response_data
                
        except Exception as e:
            logger.error(f"AdvancedRAGFlow post error: {str(e)}")
            error_response = {
                "success": False,
                "error": f"Advanced pipeline post-processing failed: {str(e)}",
                "pipeline_metadata": {
                    "pipeline_id": shared_store.get('pipeline_id', 'unknown'),
                    "pipeline_type": "advanced_rag"
                }
            }
            # Store final result in shared store for run() method
            shared_store['final_result'] = error_response
            return error_response
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete advanced RAG pipeline manually"""
        try:
            # Prepare the pipeline
            prep_result = await self.prep_async(shared_store)
            if 'error' in prep_result:
                return {
                    "success": False,
                    "error": prep_result['error'],
                    "pipeline_metadata": {"pipeline_type": "advanced_rag"}
                }
            
            logger.info(f"Advanced RAG pipeline initialized for query: {shared_store['query'][:50]}...")
            
            # Step 1: Generate query embedding
            embed_result = await self.query_embedder._run_async(shared_store)
            if not isinstance(embed_result, dict) or embed_result.get("next_state") != "success":
                return {
                    "success": False,
                    "error": "Query embedding failed",
                    "pipeline_metadata": {"pipeline_type": "advanced_rag", "failed_at": "embedding"}
                }
            
            # Step 2: Search Supabase with embeddings
            search_result = await self.supabase_search._run_async(shared_store)
            # SupabaseEdgeSearchNode returns "default" on success, "failed" on failure
            if search_result not in ["default"]:
                return {
                    "success": False,
                    "error": "Document search failed",
                    "pipeline_metadata": {"pipeline_type": "advanced_rag", "failed_at": "search"}
                }
            
            # Step 3: Re-rank results
            rerank_result = await self.re_ranker._run_async(shared_store)
            # CompactReRankerNode returns {"next_state": "reranked"} on success, {"next_state": "failed"} on failure
            if not isinstance(rerank_result, dict) or rerank_result.get("next_state") not in ["reranked"]:
                return {
                    "success": False,
                    "error": "Result re-ranking failed",
                    "pipeline_metadata": {"pipeline_type": "advanced_rag", "failed_at": "reranking"}
                }
            
            # Step 4: Generate response
            gen_result = await self.advanced_generator._run_async(shared_store)
            # AdvancedGeneratorNode returns "default" on success, "failed" on failure
            if gen_result not in ["default"]:
                return {
                    "success": False,
                    "error": "Response generation failed",
                    "pipeline_metadata": {"pipeline_type": "advanced_rag", "failed_at": "generation"}
                }
            
            # Process final results
            return await self.post_async(shared_store, prep_result, "success")
            
        except Exception as e:
            logger.error(f"AdvancedRAGFlow run error: {str(e)}")
            return {
                "success": False,
                "error": f"Advanced pipeline execution failed: {str(e)}",
                "pipeline_metadata": {
                    "pipeline_type": "advanced_rag"
                }
            }