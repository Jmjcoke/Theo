"""
LightweightHybridSearchNode - Simplified hybrid search execution.

Replacement for HybridSearchNode (186 lines) to comply with PocketFlow 150-line limit.
Focused on basic search execution without theological weighting.
"""

import logging
import os
import requests
from typing import Dict, Any
from pocketflow import AsyncNode
from ...utils.citation_utils import create_excerpt, generate_citation

logger = logging.getLogger(__name__)


class LightweightHybridSearchNode(AsyncNode):
    """Executes hybrid search via Supabase Edge Function with minimal processing."""
    
    def __init__(self, result_limit: int = 10):
        super().__init__(max_retries=3, wait=1)
        self.result_limit = result_limit
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate search query and configuration."""
        try:
            if 'query' not in shared_store:
                return {"error": "Missing required 'query' field for search"}
            
            query = shared_store['query']
            if not query or not isinstance(query, str) or len(query.strip()) == 0:
                return {"error": "Query must be a non-empty string"}
            
            # Get configuration
            edge_function_url = os.getenv('SUPABASE_EDGE_FUNCTION_URL')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            if not edge_function_url or not supabase_service_key:
                return {"error": "Edge Function configuration missing"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"LightweightHybridSearchNode prep error: {str(e)}")
            return {"error": f"Search preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute hybrid search via Edge Function."""
        try:
            query = shared_store['query'].strip()
            edge_function_url = os.getenv('SUPABASE_EDGE_FUNCTION_URL')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            # Prepare request
            headers = {
                'Authorization': f'Bearer {supabase_service_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'query': query,
                'match_count': self.result_limit
            }
            
            # Call Edge Function
            response = requests.post(
                edge_function_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                results = response.json()
                
                if not isinstance(results, list):
                    return {
                        'success': False,
                        'error': "Edge Function returned non-list results",
                        'search_results': [],
                        'result_count': 0
                    }
                
                # Format results
                formatted_results = []
                for i, r in enumerate(results):
                    if isinstance(r, dict) and r.get('content'):
                        formatted_results.append({
                            'content': r.get('content', ''),
                            'metadata': r.get('metadata', {}),
                            'similarity_score': r.get('rrf_score', 0.0),
                            'relevance': r.get('rrf_score', 0.0),
                            'document_id': str(r.get('metadata', {}).get('document_id', f'doc_{i}')),
                            'excerpt': create_excerpt(r.get('content', '')),
                            'citation': generate_citation(r.get('metadata', {}))
                        })
                
                return {
                    'success': True,
                    'search_results': formatted_results,
                    'result_count': len(formatted_results),
                    'query': query
                }
                
            else:
                error_msg = f"Edge Function failed: {response.status_code}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'search_results': [],
                    'result_count': 0
                }
                
        except Exception as e:
            error_msg = f"Search execution failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'search_results': [],
                'result_count': 0
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store search results for downstream processing."""
        try:
            exec_result = shared_store.get('exec_result', {})
            
            if exec_result.get('success', False):
                shared_store['raw_search_results'] = exec_result['search_results']
                shared_store['search_result_count'] = exec_result['result_count']
                shared_store['search_query'] = exec_result['query']
                return {"next_state": "completed"}
            else:
                error = exec_result.get('error', 'Unknown search error')
                shared_store['raw_search_results'] = []
                shared_store['search_result_count'] = 0
                shared_store['search_error'] = error
                
                logger.error(f"Search failed: {error}")
                return {"next_state": "failed"}
                
        except Exception as e:
            error_msg = f"Search post processing failed: {str(e)}"
            logger.error(error_msg)
            shared_store['raw_search_results'] = []
            shared_store['search_result_count'] = 0
            shared_store['search_error'] = error_msg
            return {"next_state": "failed"}