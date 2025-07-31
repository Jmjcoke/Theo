"""
HybridSearchNode - Pure search execution via Supabase Edge Function

Focused responsibility: Execute hybrid search and return raw results.
Part of the split from oversized SupabaseEdgeSearchNode.
"""

import logging
import os
import requests
from typing import Dict, Any, List
from pocketflow import AsyncNode
from ...utils.citation_utils import create_excerpt, generate_citation


class HybridSearchNode(AsyncNode):
    """Executes hybrid search via Supabase Edge Function"""
    
    def __init__(self, result_limit: int = 10):
        """Initialize the search node"""
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
                raise ValueError("Missing required 'query' field for search")
            
            query = shared_store['query']
            if not query or not isinstance(query, str) or len(query.strip()) == 0:
                raise ValueError("Query must be a non-empty string")
            
            # Check Edge Function configuration
            if not self.edge_function_url:
                raise ValueError("SUPABASE_EDGE_FUNCTION_URL not configured")
            
            if not self.supabase_service_key:
                raise ValueError("SUPABASE_SERVICE_KEY not configured")
            
            # Return validated data for exec_async
            return {
                'validated_query': query.strip(),
                'edge_function_url': self.edge_function_url,
                'supabase_service_key': self.supabase_service_key,
                'result_limit': self.result_limit,
                'timeout': 15
            }
            
        except Exception as e:
            error_msg = f"Search prep failed: {str(e)}"
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
            
            # Call Edge Function
            timeout = prep_result.get('timeout', 15)
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
                
                # Basic formatting for pipeline compatibility
                formatted_results = []
                for i, result in enumerate(results):
                    if not isinstance(result, dict):
                        self.logger.warning(f"Skipping invalid result {i}")
                        continue
                    
                    content = result.get('content', '')
                    metadata = result.get('metadata', {})
                    rrf_score = result.get('rrf_score', 0.0)
                    
                    if not content:
                        self.logger.warning(f"Skipping result {i}: empty content")
                        continue
                    
                    # Minimal formatting - enrichment happens in parallel nodes
                    formatted_result = {
                        'content': content,
                        'metadata': metadata,
                        'similarity_score': rrf_score,
                        'relevance': rrf_score,
                        'document_id': str(metadata.get('document_id', f'doc_{i}')),
                        'excerpt': create_excerpt(content),
                        'citation': generate_citation(metadata)
                    }
                    
                    formatted_results.append(formatted_result)
                
                self.logger.info(f"Search completed: {len(formatted_results)} results")
                
                return {
                    'success': True,
                    'search_results': formatted_results,
                    'result_count': len(formatted_results),
                    'query': query
                }
                
            else:
                error_msg = f"Edge Function failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'search_results': [],
                    'result_count': 0
                }
                
        except Exception as e:
            error_msg = f"Search execution failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'search_results': [],
                'result_count': 0
            }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """Store search results for downstream nodes"""
        try:
            if exec_result.get('success', False):
                # Store raw search results for parallel processing
                shared_store['raw_search_results'] = exec_result['search_results']
                shared_store['search_result_count'] = exec_result['result_count']
                shared_store['search_query'] = exec_result['query']
                
                self.logger.info(f"Search successful: {exec_result['result_count']} results")
                return "default"
            else:
                # Handle search failure
                error = exec_result.get('error', 'Unknown search error')
                shared_store['raw_search_results'] = []
                shared_store['search_result_count'] = 0
                shared_store['search_error'] = error
                
                self.logger.error(f"Search failed: {error}")
                return "failed"
                
        except Exception as e:
            error_msg = f"Search post processing failed: {str(e)}"
            self.logger.error(error_msg)
            shared_store['raw_search_results'] = []
            shared_store['search_result_count'] = 0
            shared_store['search_error'] = error_msg
            return "failed"