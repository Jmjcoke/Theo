"""
TheologicalWeightingNode - Applies domain-specific theological weighting to search results

Focused responsibility: Apply theological categorization and authority-based scoring.
Can run in parallel with metadata enrichment for better performance.
Part of the split from oversized SupabaseEdgeSearchNode.
"""

import logging
from typing import Dict, Any, List
from pocketflow import AsyncNode
from ...utils.theological_metadata import TheologicalMetadata


class TheologicalWeightingNode(AsyncNode):
    """Applies theological weighting and categorization to search results"""
    
    def __init__(self):
        """Initialize the theological weighting node"""
        super().__init__(max_retries=2, wait=0.5)
        self.logger = logging.getLogger(__name__)
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate enriched results are available for theological weighting"""
        try:
            # Check for enriched results from MetadataEnrichmentNode
            if 'metadata_enriched_results' not in shared_store:
                # Fallback to raw search results if enrichment hasn't completed
                if 'raw_search_results' not in shared_store:
                    raise ValueError("No search results available for theological weighting")
                
                search_results = shared_store.get('raw_search_results', [])
                self.logger.info("Using raw search results (enrichment not yet available)")
            else:
                search_results = shared_store.get('metadata_enriched_results', [])
                self.logger.info("Using metadata-enriched results for theological weighting")
            
            if not isinstance(search_results, list):
                raise ValueError("Search results must be a list")
            
            if len(search_results) == 0:
                self.logger.info("No search results to weight theologically")
                return {'search_results': [], 'skip_weighting': True}
            
            self.logger.info(f"Preparing theological weighting for {len(search_results)} results")
            
            return {
                'search_results': search_results,
                'skip_weighting': False
            }
            
        except Exception as e:
            error_msg = f"Theological weighting prep failed: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply theological weighting and categorization"""
        try:
            # Skip weighting if no results
            if prep_result.get('skip_weighting', False):
                return {
                    'success': True,
                    'weighted_results': [],
                    'theological_analysis': {
                        'olson_sources': 0,
                        'biblical_sources': 0,
                        'total_sources': 0
                    }
                }
            
            search_results = prep_result['search_results']
            
            self.logger.info(f"Starting theological weighting for {len(search_results)} results")
            
            # Apply theological weighting and reorder by authority + relevance
            weighted_results = TheologicalMetadata.weight_search_results(search_results)
            
            # Analyze theological distribution
            olson_sources = sum(1 for r in weighted_results 
                              if r.get('theological_category') == 'GORDON_OLSON_PRIMARY')
            biblical_sources = sum(1 for r in weighted_results 
                                 if r.get('theological_category') == 'BIBLICAL_TEXT')
            
            theological_analysis = {
                'olson_sources': olson_sources,
                'biblical_sources': biblical_sources,
                'total_sources': len(weighted_results),
                'weighting_applied': True
            }
            
            self.logger.info(f"Theological weighting completed: {olson_sources} Olson sources, {biblical_sources} biblical sources")
            
            return {
                'success': True,
                'weighted_results': weighted_results,
                'theological_analysis': theological_analysis
            }
            
        except Exception as e:
            error_msg = f"Theological weighting execution failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'weighted_results': prep_result.get('search_results', []),
                'theological_analysis': {
                    'olson_sources': 0,
                    'biblical_sources': 0,
                    'total_sources': 0,
                    'weighting_applied': False
                }
            }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """Store final weighted results for the RAG pipeline"""
        try:
            if exec_result.get('success', False):
                # Store final weighted results
                shared_store['search_results'] = exec_result['weighted_results']
                shared_store['result_count'] = len(exec_result['weighted_results'])
                shared_store['theological_analysis'] = exec_result['theological_analysis']
                shared_store['search_method'] = 'hybrid_theological_parallel'
                
                analysis = exec_result['theological_analysis']
                self.logger.info(f"Theological weighting successful: {analysis['olson_sources']} Olson, {analysis['biblical_sources']} biblical sources")
                
                return "default"
            else:
                # Handle weighting failure - pass through unweighted results
                error = exec_result.get('error', 'Unknown weighting error')
                shared_store['search_results'] = exec_result.get('weighted_results', [])
                shared_store['result_count'] = len(shared_store['search_results'])
                shared_store['theological_analysis'] = exec_result.get('theological_analysis', {})
                shared_store['weighting_error'] = error
                
                self.logger.warning(f"Theological weighting failed: {error}")
                return "failed"
                
        except Exception as e:
            error_msg = f"Theological weighting post processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Ensure clean state on error
            shared_store['search_results'] = prep_result.get('search_results', [])
            shared_store['result_count'] = len(shared_store['search_results'])
            shared_store['theological_analysis'] = {}
            shared_store['weighting_error'] = error_msg
            
            return "failed"