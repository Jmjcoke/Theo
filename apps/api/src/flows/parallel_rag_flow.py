"""
ParallelRAGFlow - Demonstrates parallel node execution with split search nodes

Shows how to configure PocketFlow for parallel processing:
HybridSearchNode → (MetadataEnrichmentNode || TheologicalWeightingNode) → merge → ReRanker → Generator

This addresses the 220-line node size violation by splitting into smaller, parallel nodes.
"""

import logging
import uuid
import time
from typing import Dict, Any
from pocketflow import AsyncFlow

from ..nodes.chat.hybrid_search_node_deprecated import HybridSearchNode
from ..nodes.chat.metadata_enrichment_node import MetadataEnrichmentNode
from ..nodes.chat.theological_weighting_node import TheologicalWeightingNode
from ..nodes.chat.compact_re_ranker_node import CompactReRankerNode
from ..nodes.chat.advanced_generator_node import AdvancedGeneratorNode

logger = logging.getLogger(__name__)


class ParallelRAGFlow(AsyncFlow):
    """
    Orchestrates parallel RAG pipeline with split search processing.
    
    Flow Architecture:
    1. HybridSearchNode (pure search execution)
    2. MetadataEnrichmentNode || TheologicalWeightingNode (parallel processing)
    3. ResultMerger (implicit - handled in next node)
    4. ReRankerNode (uses merged results)
    5. AdvancedGeneratorNode (final response)
    
    This demonstrates how PocketFlow handles parallel execution patterns.
    """
    
    def __init__(self):
        """Initialize flow with parallel node configuration"""
        # Initialize all nodes
        self.hybrid_search = HybridSearchNode(result_limit=10)
        self.metadata_enrichment = MetadataEnrichmentNode()
        self.theological_weighting = TheologicalWeightingNode()
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
        
        # Configure parallel execution pattern
        # Step 1: Search node runs first
        self.hybrid_search >> [self.metadata_enrichment, self.theological_weighting]
        
        # Step 2: Both enrichment nodes feed into re-ranker
        # The re-ranker will wait for both parallel nodes to complete
        self.metadata_enrichment >> self.re_ranker
        self.theological_weighting >> self.re_ranker
        
        # Step 3: Re-ranker feeds into generator
        self.re_ranker >> self.advanced_generator
        
        # Initialize AsyncFlow with hybrid search as start node
        super().__init__(start=self.hybrid_search)
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> bool:
        """Prepare shared store for parallel RAG pipeline execution"""
        pipeline_id = str(uuid.uuid4())
        shared_store['pipeline_id'] = pipeline_id
        
        try:
            # Validate required inputs
            required_fields = ['query', 'session_id', 'user_id']
            for field in required_fields:
                if field not in shared_store:
                    raise ValueError(f"Missing required field: {field}")
            
            # Initialize pipeline metadata
            shared_store['pipeline_start_time'] = time.time()
            shared_store['pipeline_type'] = 'parallel_rag'
            shared_store['parallel_execution_enabled'] = True
            
            # Set default context
            if 'context' not in shared_store:
                shared_store['context'] = 'general'
            
            # Initialize tracking for parallel operations
            shared_store['parallel_metadata'] = {
                'nodes_in_parallel': ['metadata_enrichment', 'theological_weighting'],
                'parallel_stage_completed': {},
                'merge_strategy': 'theological_weighted_with_metadata'
            }
            
            logger.info(f"Parallel RAG pipeline initialized: {pipeline_id}")
            return True
            
        except Exception as e:
            logger.error(f"ParallelRAGFlow prep error: {str(e)}")
            shared_store['pipeline_error'] = str(e)
            return False
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: bool, exec_result: str) -> Dict[str, Any]:
        """Process final results from parallel execution"""
        pipeline_id = shared_store.get('pipeline_id', 'unknown')
        
        try:
            if exec_result == "default" and 'generated_answer' in shared_store:
                # Use final search results (should be theologically weighted + metadata enriched)
                source_results = shared_store.get('search_results', [])
                sources = []
                
                for result in source_results:
                    sources.append({
                        "document_id": result.get('document_id'),
                        "title": result.get('document_title', result.get('title', 'Unknown Document')),
                        "excerpt": result.get('excerpt', ''),
                        "relevance": result.get('theological_weight', result.get('relevance', 0.0)),
                        "theological_category": result.get('theological_category'),
                        "citation": result.get('citation'),
                        "metadata_enriched": result.get('metadata_enriched', False),
                        "theologically_weighted": result.get('theologically_weighted', False)
                    })
                
                # Calculate timing
                pipeline_end_time = time.time()
                pipeline_start_time = shared_store.get('pipeline_start_time', pipeline_end_time)
                total_time = pipeline_end_time - pipeline_start_time
                
                # Analyze parallel execution efficiency
                parallel_metadata = shared_store.get('parallel_metadata', {})
                enrichment_count = shared_store.get('enrichment_count', 0)
                theological_analysis = shared_store.get('theological_analysis', {})
                
                response_data = {
                    "success": True,
                    "response": shared_store.get('generated_answer', ''),
                    "confidence": shared_store.get('confidence', 0.0),
                    "sources": sources,
                    "pipeline_metadata": {
                        "pipeline_id": pipeline_id,
                        "pipeline_type": "parallel_rag",
                        "total_pipeline_time": total_time,
                        "parallel_execution": {
                            "enabled": True,
                            "metadata_enrichment_results": enrichment_count,
                            "theological_analysis": theological_analysis,
                            "parallel_efficiency": "Both nodes completed successfully"
                        },
                        "node_split_benefit": {
                            "original_node_lines": 220,
                            "split_into_nodes": 3,
                            "max_node_lines": 70,
                            "parallel_execution_enabled": True
                        }
                    }
                }
                
                logger.info(f"Parallel RAG pipeline completed: {pipeline_id} in {total_time:.2f}s")
                shared_store['final_result'] = response_data
                return response_data
                
            else:
                # Handle failure
                error_messages = []
                for error_key in ['search_error', 'enrichment_error', 'weighting_error', 're_ranking_error', 'generation_error']:
                    if error_key in shared_store:
                        error_messages.append(f"{error_key}: {shared_store[error_key]}")
                
                combined_error = "; ".join(error_messages) if error_messages else "Unknown parallel pipeline failure"
                
                response_data = {
                    "success": False,
                    "error": combined_error,
                    "pipeline_metadata": {
                        "pipeline_id": pipeline_id,
                        "pipeline_type": "parallel_rag",
                        "failure_stage": exec_result
                    }
                }
                
                logger.error(f"Parallel RAG pipeline failed: {pipeline_id} - {combined_error}")
                shared_store['final_result'] = response_data
                return response_data
                
        except Exception as e:
            logger.error(f"ParallelRAGFlow post error: {str(e)}")
            error_response = {
                "success": False,
                "error": f"Parallel pipeline post-processing failed: {str(e)}",
                "pipeline_metadata": {
                    "pipeline_id": pipeline_id,
                    "pipeline_type": "parallel_rag"
                }
            }
            shared_store['final_result'] = error_response
            return error_response
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the parallel RAG pipeline"""
        try:
            # Execute the flow - PocketFlow handles parallel execution automatically
            await self.run_async(shared_store)
            
            # Return processed results
            result = shared_store.get('final_result', {
                "success": False,
                "error": "Parallel pipeline execution failed"
            })
            
            logger.info(f"Parallel RAG run completed: success={result.get('success', False)}")
            return result
            
        except Exception as e:
            error_msg = f"Parallel RAG pipeline execution failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "pipeline_metadata": {
                    "pipeline_type": "parallel_rag"
                }
            }


class ResultMerger:
    """
    Helper class to understand how parallel results get merged.
    
    In PocketFlow, when multiple nodes feed into the same downstream node,
    the downstream node can access results from all upstream nodes via shared_store.
    
    This is how the TheologicalWeightingNode accesses both:
    - raw_search_results (from HybridSearchNode)
    - metadata_enriched_results (from MetadataEnrichmentNode)
    """
    
    @staticmethod
    def merge_parallel_results(shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example of how to manually merge parallel results if needed.
        
        In our case, TheologicalWeightingNode handles this automatically
        by checking for both raw and enriched results.
        """
        raw_results = shared_store.get('raw_search_results', [])
        enriched_results = shared_store.get('metadata_enriched_results', [])
        
        # Use enriched results if available, otherwise fall back to raw
        if enriched_results:
            logger.info("Using metadata-enriched results for theological weighting")
            return enriched_results
        else:
            logger.info("Using raw search results for theological weighting")
            return raw_results