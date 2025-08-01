"""
SearchResultsProcessorNode for processing and enriching search results.

Split from supabase_edge_search_node.py to comply with PocketFlow 150-line limit.
Handles the post phase of search result processing and theological weighting.
"""

import logging
from typing import Dict, Any
from pocketflow import AsyncNode
from ...utils.citation_utils import enrich_search_results_with_metadata
from ...utils.theological_metadata import TheologicalMetadata

logger = logging.getLogger(__name__)


class SearchResultsProcessorNode(AsyncNode):
    """Processes and enriches search results with theological weighting."""
    
    def __init__(self):
        super().__init__()
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Prepare for search results processing."""
        try:
            # Check that Edge Function call was successful
            if not shared_store.get('raw_results'):
                return {"error": "No raw results available for processing"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"SearchResultsProcessorNode prep error: {str(e)}")
            return {"error": f"Search results processing preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute search results processing and theological weighting."""
        try:
            raw_results = shared_store['raw_results']
            query = shared_store.get('query', '')
            
            # Enrich results with SQLite document metadata
            enriched_results = enrich_search_results_with_metadata(raw_results)
            
            # Apply theological weighting and reorder by authority + relevance
            theologically_weighted_results = TheologicalMetadata.weight_search_results(enriched_results)
            
            # Log theological analysis
            olson_sources = sum(1 for r in theologically_weighted_results 
                              if r.get('theological_category') == 'GORDON_OLSON_PRIMARY')
            biblical_sources = sum(1 for r in theologically_weighted_results 
                                 if r.get('theological_category') == 'BIBLICAL_TEXT')
            
            logger.info(f"Theological weighting applied: {olson_sources} Olson sources, {biblical_sources} biblical sources")
            
            return {
                'success': True,
                'search_results': theologically_weighted_results,
                'result_count': len(theologically_weighted_results),
                'search_method': 'edge_function_hybrid_theological',
                'query': query,
                'theological_stats': {
                    'olson_sources': olson_sources,
                    'biblical_sources': biblical_sources,
                    'total_results': len(theologically_weighted_results)
                }
            }
            
        except Exception as e:
            error_msg = f"Search results processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'search_results': [],
                'result_count': 0
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store final processed results in shared store."""
        try:
            # Get execution results
            exec_result = shared_store.get('exec_result', {})
            
            if exec_result.get('success', False):
                # Store search results in shared store for downstream nodes
                shared_store['search_results'] = exec_result['search_results']
                shared_store['result_count'] = exec_result['result_count']
                shared_store['search_method'] = exec_result['search_method']
                shared_store['theological_stats'] = exec_result.get('theological_stats', {})
                
                # Create summary for logging
                search_results = exec_result['search_results']
                result_count = exec_result['result_count']
                
                top_score = search_results[0]['similarity_score'] if search_results else 0.0
                
                logger.info(f"Search results processing successful: {result_count} results, top score: {top_score:.3f}")
                
                return {"next_state": "completed"}
            else:
                # Handle processing failure
                error = exec_result.get('error', 'Unknown processing error')
                
                # Ensure empty results are set in shared store
                shared_store['search_results'] = []
                shared_store['result_count'] = 0
                shared_store['search_error'] = error
                
                logger.error(f"Search results processing failed: {error}")
                return {"next_state": "failed"}
                
        except Exception as e:
            error_msg = f"Search results post processing failed: {str(e)}"
            logger.error(error_msg)
            
            # Ensure clean state on error
            shared_store['search_results'] = []
            shared_store['result_count'] = 0
            shared_store['search_error'] = error_msg
            
            return {"next_state": "failed"}