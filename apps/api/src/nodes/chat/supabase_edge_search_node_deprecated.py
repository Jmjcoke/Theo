"""
SupabaseEdgeSearchNode for hybrid search using your Supabase Edge Function

Calls your Supabase Edge Function which handles:
1. Query embedding generation via OpenAI
2. Hybrid search (full-text + semantic) in Supabase
3. Returns formatted results for RAG pipeline
"""

import logging
import os
import requests
from typing import Dict, Any, List
from pocketflow import AsyncNode
from ...utils.citation_utils import create_excerpt, generate_citation, enrich_search_results_with_metadata
from ...utils.theological_metadata import TheologicalMetadata


class SupabaseEdgeSearchNode(AsyncNode):
    """Performs hybrid search via Supabase Edge Function"""
    
    def __init__(self, result_limit: int = 10):
        """Initialize the Edge Function search node"""
        super().__init__(max_retries=3, wait=1)
        self.logger = logging.getLogger(__name__)
        self.result_limit = result_limit
        
        # Get Edge Function configuration
        self.edge_function_url = os.getenv('SUPABASE_EDGE_FUNCTION_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.edge_function_url:
            self.logger.warning("SUPABASE_EDGE_FUNCTION_URL not configured")
        if not self.supabase_service_key:
            self.logger.warning("SUPABASE_SERVICE_KEY not configured")
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate query and Edge Function configuration"""
        try:
            # Check for required query
            if 'query' not in shared_store:
                raise ValueError("Missing required 'query' field for Edge Function search")
            
            query = shared_store['query']
            if not query or not isinstance(query, str) or len(query.strip()) == 0:
                raise ValueError("Query must be a non-empty string")
            
            # Check Edge Function configuration
            if not self.edge_function_url:
                raise ValueError("SUPABASE_EDGE_FUNCTION_URL not configured")
            
            if not self.supabase_service_key:
                raise ValueError("SUPABASE_SERVICE_KEY not configured")
            
            # Return validated data for exec_async
            validated_data = {
                'validated_query': query.strip(),
                'edge_function_url': self.edge_function_url,
                'supabase_service_key': self.supabase_service_key,
                'result_limit': self.result_limit,
                'timeout': 15  # Configurable timeout instead of hardcoded 30s
            }
            
            self.logger.info(f"Edge Function search prepared for query: {query[:50]}...")
            return validated_data
            
        except Exception as e:
            error_msg = f"Edge Function search prep failed: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hybrid search via Edge Function"""
        try:
            query = prep_result['validated_query']
            edge_function_url = prep_result['edge_function_url']
            supabase_service_key = prep_result['supabase_service_key']
            result_limit = prep_result['result_limit']
            
            # Prepare Edge Function request
            headers = {
                'Authorization': f'Bearer {supabase_service_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'query': query,
                'match_count': result_limit
            }
            
            self.logger.info(f"Calling Edge Function: {edge_function_url}")
            
            # Call your Edge Function with configurable timeout
            timeout = prep_result.get('timeout', 15)  # Reduced from 30s to 15s default
            response = requests.post(
                edge_function_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # Validate results format
                if not isinstance(results, list):
                    raise ValueError("Edge Function returned non-list results")
                
                # Process and format results for RAG pipeline
                formatted_results = []
                for i, result in enumerate(results):
                    if not isinstance(result, dict):
                        self.logger.warning(f"Skipping invalid result {i}: not a dictionary")
                        continue
                    
                    # Extract fields from your Edge Function response
                    content = result.get('content', '')
                    metadata = result.get('metadata', {})
                    rrf_score = result.get('rrf_score', 0.0)
                    
                    if not content:
                        self.logger.warning(f"Skipping result {i}: empty content")
                        continue
                    
                    # Format for RAG pipeline
                    formatted_result = {
                        'content': content,
                        'metadata': metadata,
                        'similarity_score': rrf_score,
                        'relevance': rrf_score,  # Add relevance field for compatibility
                        'document_id': str(metadata.get('document_id', f'doc_{i}')),
                        'excerpt': create_excerpt(content),
                        'citation': generate_citation(metadata)
                    }
                    
                    formatted_results.append(formatted_result)
                
                # Enrich results with SQLite document metadata
                enriched_results = enrich_search_results_with_metadata(formatted_results)
                
                # Apply theological weighting and reorder by authority + relevance
                theologically_weighted_results = TheologicalMetadata.weight_search_results(enriched_results)
                
                # Log theological analysis
                olson_sources = sum(1 for r in theologically_weighted_results 
                                  if r.get('theological_category') == 'GORDON_OLSON_PRIMARY')
                biblical_sources = sum(1 for r in theologically_weighted_results 
                                     if r.get('theological_category') == 'BIBLICAL_TEXT')
                
                self.logger.info(f"Theological weighting applied: {olson_sources} Olson sources, {biblical_sources} biblical sources")
                self.logger.info(f"Edge Function search completed: {len(formatted_results)} results with enhanced metadata")
                
                return {
                    'success': True,
                    'search_results': theologically_weighted_results,
                    'result_count': len(theologically_weighted_results),
                    'search_method': 'edge_function_hybrid_theological',
                    'query': query
                }
                
            else:
                error_msg = f"Edge Function call failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'search_results': [],
                    'result_count': 0
                }
                
        except Exception as e:
            error_msg = f"Edge Function search execution failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'search_results': [],
                'result_count': 0
            }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """Process search results and prepare response"""
        try:
            if exec_result.get('success', False):
                # Store search results in shared store for downstream nodes
                shared_store['search_results'] = exec_result['search_results']
                shared_store['result_count'] = exec_result['result_count']
                shared_store['search_method'] = exec_result['search_method']
                
                # Create summary for logging/debugging
                search_results = exec_result['search_results']
                result_count = exec_result['result_count']
                query = exec_result['query']
                
                top_score = search_results[0]['similarity_score'] if search_results else 0.0
                
                self.logger.info(f"Edge Function search successful: {result_count} results, top score: {top_score:.3f}")
                
                return "default"
            else:
                # Handle search failure
                error = exec_result.get('error', 'Unknown search error')
                
                # Ensure empty results are set in shared store
                shared_store['search_results'] = []
                shared_store['result_count'] = 0
                shared_store['search_error'] = error
                
                self.logger.error(f"Edge Function search failed: {error}")
                return "failed"
                
        except Exception as e:
            error_msg = f"Edge Function search post processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Ensure clean state on error
            shared_store['search_results'] = []
            shared_store['result_count'] = 0
            shared_store['search_error'] = error_msg
            
            return "failed"