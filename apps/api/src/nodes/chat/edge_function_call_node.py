"""
EdgeFunctionCallNode for making hybrid search calls to Supabase Edge Function.

Split from supabase_edge_search_node.py to comply with PocketFlow 150-line limit.
Handles the exec phase of Edge Function communication and result formatting.
"""

import logging
import requests
from typing import Dict, Any
from pocketflow import AsyncNode
from ...utils.citation_utils import create_excerpt, generate_citation

logger = logging.getLogger(__name__)


class EdgeFunctionCallNode(AsyncNode):
    """Makes calls to Supabase Edge Function and formats results."""
    
    def __init__(self):
        super().__init__(max_retries=3, wait=1)
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Prepare for Edge Function call."""
        try:
            # Check that validation was successful
            if not shared_store.get('validated_data'):
                return {"error": "Query validation failed - cannot proceed with Edge Function call"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"EdgeFunctionCallNode prep error: {str(e)}")
            return {"error": f"Edge Function call preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute hybrid search via Edge Function."""
        try:
            validated_data = shared_store['validated_data']
            query = validated_data['validated_query']
            edge_function_url = validated_data['edge_function_url']
            supabase_service_key = validated_data['supabase_service_key']
            result_limit = validated_data['result_limit']
            timeout = validated_data.get('timeout', 15)
            
            # Prepare Edge Function request
            headers = {
                'Authorization': f'Bearer {supabase_service_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'query': query,
                'match_count': result_limit
            }
            
            logger.info(f"Calling Edge Function: {edge_function_url}")
            
            # Call Edge Function
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
                    return {
                        'success': False,
                        'error': "Edge Function returned non-list results",
                        'raw_results': []
                    }
                
                # Process and format results
                formatted_results = self._format_search_results(results)
                
                logger.info(f"Edge Function call successful: {len(formatted_results)} results")
                
                return {
                    'success': True,
                    'raw_results': formatted_results,
                    'result_count': len(formatted_results),
                    'query': query
                }
                
            else:
                error_msg = f"Edge Function call failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'raw_results': [],
                    'result_count': 0
                }
                
        except Exception as e:
            error_msg = f"Edge Function call execution failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'raw_results': [],
                'result_count': 0
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store Edge Function call results for downstream processing."""
        try:
            # Results are stored by the framework
            logger.info("Edge Function call completed")
            return {"next_state": "called"}
            
        except Exception as e:
            logger.error(f"EdgeFunctionCallNode post error: {str(e)}")
            return {"next_state": "failed"}
    
    def _format_search_results(self, results: list) -> list:
        """Format raw Edge Function results for RAG pipeline."""
        formatted_results = []
        
        for i, result in enumerate(results):
            if not isinstance(result, dict) or not result.get('content'):
                continue
            
            # Extract and format fields
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            rrf_score = result.get('rrf_score', 0.0)
            
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
        
        return formatted_results