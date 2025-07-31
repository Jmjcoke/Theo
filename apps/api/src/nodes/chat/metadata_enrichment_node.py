"""
MetadataEnrichmentNode - Enriches search results with SQLite document metadata

Focused responsibility: Add document titles, page numbers, and metadata from SQLite.
Can run in parallel with theological weighting for better performance.
Part of the split from oversized SupabaseEdgeSearchNode.
"""

import logging
from typing import Dict, Any, List
from pocketflow import AsyncNode
from ...utils.citation_utils import enrich_search_results_with_metadata


class MetadataEnrichmentNode(AsyncNode):
    """Enriches search results with SQLite document metadata"""
    
    def __init__(self, sqlite_db_path: str = "theo.db"):
        """Initialize the enrichment node"""
        super().__init__(max_retries=2, wait=0.5)
        self.logger = logging.getLogger(__name__)
        self.sqlite_db_path = sqlite_db_path
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search results are available for enrichment"""
        try:
            # Check for search results from HybridSearchNode
            if 'raw_search_results' not in shared_store:
                raise ValueError("No raw search results available for enrichment")
            
            search_results = shared_store.get('raw_search_results', [])
            if not isinstance(search_results, list):
                raise ValueError("Search results must be a list")
            
            if len(search_results) == 0:
                self.logger.info("No search results to enrich")
                return {'search_results': [], 'skip_enrichment': True}
            
            self.logger.info(f"Preparing to enrich {len(search_results)} search results")
            
            return {
                'search_results': search_results,
                'sqlite_db_path': self.sqlite_db_path,
                'skip_enrichment': False
            }
            
        except Exception as e:
            error_msg = f"Metadata enrichment prep failed: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich search results with SQLite metadata"""
        try:
            # Skip enrichment if no results
            if prep_result.get('skip_enrichment', False):
                return {
                    'success': True,
                    'enriched_results': [],
                    'enrichment_count': 0
                }
            
            search_results = prep_result['search_results']
            sqlite_db_path = prep_result['sqlite_db_path']
            
            self.logger.info(f"Starting metadata enrichment for {len(search_results)} results")
            
            # Perform metadata enrichment
            enriched_results = enrich_search_results_with_metadata(
                search_results, 
                sqlite_db_path
            )
            
            # Count how many results were actually enriched
            enrichment_count = 0
            for result in enriched_results:
                if result.get('document_title') or result.get('title'):
                    enrichment_count += 1
            
            self.logger.info(f"Metadata enrichment completed: {enrichment_count}/{len(enriched_results)} results enriched")
            
            return {
                'success': True,
                'enriched_results': enriched_results,
                'enrichment_count': enrichment_count,
                'total_results': len(enriched_results)
            }
            
        except Exception as e:
            error_msg = f"Metadata enrichment execution failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'enriched_results': prep_result.get('search_results', []),
                'enrichment_count': 0
            }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """Store enriched results for downstream processing"""
        try:
            if exec_result.get('success', False):
                # Store enriched results for theological weighting
                shared_store['metadata_enriched_results'] = exec_result['enriched_results']
                shared_store['enrichment_count'] = exec_result['enrichment_count']
                
                enrichment_count = exec_result.get('enrichment_count', 0)
                total_results = exec_result.get('total_results', 0)
                
                self.logger.info(f"Metadata enrichment successful: {enrichment_count}/{total_results} results enriched")
                return "default"
            else:
                # Handle enrichment failure - pass through original results
                error = exec_result.get('error', 'Unknown enrichment error')
                shared_store['metadata_enriched_results'] = exec_result.get('enriched_results', [])
                shared_store['enrichment_count'] = 0
                shared_store['enrichment_error'] = error
                
                self.logger.warning(f"Metadata enrichment failed: {error}")
                return "failed"
                
        except Exception as e:
            error_msg = f"Metadata enrichment post processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Ensure clean state on error
            shared_store['metadata_enriched_results'] = prep_result.get('search_results', [])
            shared_store['enrichment_count'] = 0
            shared_store['enrichment_error'] = error_msg
            
            return "failed"