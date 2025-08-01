"""
QueryValidationNode for validating search queries and Edge Function configuration.

Split from supabase_edge_search_node.py to comply with PocketFlow 150-line limit.
Handles the prep phase of hybrid search validation.
"""

import logging
import os
from typing import Dict, Any
from pocketflow import AsyncNode

logger = logging.getLogger(__name__)


class QueryValidationNode(AsyncNode):
    """Validates search queries and Edge Function configuration."""
    
    def __init__(self, result_limit: int = 10):
        super().__init__(max_retries=3, wait=1)
        self.result_limit = result_limit
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Prepare for query validation."""
        try:
            # Basic validation that required fields exist
            if 'query' not in shared_store:
                return {"error": "Missing required 'query' field for search validation"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"QueryValidationNode prep error: {str(e)}")
            return {"error": f"Query validation preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute query validation and Edge Function configuration check."""
        try:
            # Get and validate query
            query = shared_store['query']
            if not query or not isinstance(query, str) or len(query.strip()) == 0:
                return {
                    'success': False,
                    'error': "Query must be a non-empty string"
                }
            
            # Get Edge Function configuration
            edge_function_url = os.getenv('SUPABASE_EDGE_FUNCTION_URL')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            # Check Edge Function configuration
            if not edge_function_url:
                return {
                    'success': False,
                    'error': "SUPABASE_EDGE_FUNCTION_URL not configured"
                }
            
            if not supabase_service_key:
                return {
                    'success': False,
                    'error': "SUPABASE_SERVICE_KEY not configured"
                }
            
            # Return validated configuration
            validated_data = {
                'validated_query': query.strip(),
                'edge_function_url': edge_function_url,
                'supabase_service_key': supabase_service_key,
                'result_limit': self.result_limit,
                'timeout': 15
            }
            
            logger.info(f"Query validation successful for: {query[:50]}...")
            
            return {
                'success': True,
                'validated_data': validated_data
            }
            
        except Exception as e:
            error_msg = f"Query validation failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store validation results for downstream processing."""
        try:
            # Validation results are stored by the framework
            logger.info("Query validation completed")
            return {"next_state": "validated"}
            
        except Exception as e:
            logger.error(f"QueryValidationNode post error: {str(e)}")
            return {"next_state": "failed"}