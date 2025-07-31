"""
QueryEmbedderNode for generating embeddings from user queries using OpenAI

Following PocketFlow AsyncNode pattern for OpenAI API integration.
Handles user queries and generates 1536-dimensional embeddings for vector search.
"""

from typing import Dict, Any
from pocketflow import AsyncNode
from ...utils.embedding_utils import EmbeddingUtils
import logging

logger = logging.getLogger(__name__)


class QueryEmbedderNode(AsyncNode):
    """Generates vector embeddings for user queries using OpenAI API following PocketFlow patterns"""
    
    def __init__(self):
        """Initialize the query embedder node"""
        super().__init__(max_retries=3, wait=1)
        self.embedding_utils = EmbeddingUtils()
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate query data and API configuration"""
        try:
            # Check for required query
            if 'query' not in shared_store:
                return {"error": "Missing required 'query' field"}
            
            query = shared_store['query']
            if not query or not isinstance(query, str):
                return {"error": "Query must be a non-empty string"}
            
            # Validate query length (max 8192 tokens for text-embedding-ada-002)
            if len(query) > 8192:
                return {"error": "Query too long for embedding model"}
            
            # Sanitize query text
            sanitized_query = query.strip()
            if not sanitized_query:
                return {"error": "Query cannot be empty after sanitization"}
            
            return {"sanitized_query": sanitized_query}
            
        except Exception as e:
            logger.error(f"QueryEmbedderNode prep error: {str(e)}")
            return {"error": f"Query preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: dict) -> Dict[str, Any]:
        """Generate embedding for the query"""
        if "error" in prep_result:
            return {"success": False, "error": prep_result["error"]}
        
        try:
            # Use prep_result data instead of accessing shared_store
            query = prep_result.get('sanitized_query')
            
            # Generate embedding using utility
            embedding_result = await self.embedding_utils.generate_embedding(query)
            
            if not embedding_result.get('success', False):
                return {
                    "success": False,
                    "error": f"Embedding generation failed: {embedding_result.get('error', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "query_embedding": embedding_result['embedding'],
                "embedding_dimensions": len(embedding_result['embedding']),
                "model_used": embedding_result.get('model', 'text-embedding-ada-002')
            }
            
        except Exception as e:
            logger.error(f"QueryEmbedderNode exec error: {str(e)}")
            return {"success": False, "error": f"Embedding execution failed: {str(e)}"}
    
    async def exec_fallback_async(self, prep_result: dict, exc: Exception) -> Dict[str, Any]:
        """Fallback for embedding failures after retries"""
        logger.error(f"QueryEmbedderNode failed after retries: {str(exc)}")
        return {
            "success": False,
            "error": "Query embedding failed after multiple retries",
            "retry_count": self.max_retries
        }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: dict, exec_result: Dict[str, Any]) -> dict:
        """Update shared store with embedding results"""
        try:
            if exec_result.get('success', False):
                # Store embedding results in shared store
                shared_store['query_embedding'] = exec_result['query_embedding']
                shared_store['embedding_dimensions'] = exec_result['embedding_dimensions']
                shared_store['embedding_model'] = exec_result.get('model_used', 'text-embedding-ada-002')
                
                logger.info(f"Query embedding generated successfully: {exec_result['embedding_dimensions']} dimensions")
                return {"next_state": "success"}
            else:
                # Store error information
                shared_store['embedding_error'] = exec_result.get('error', 'Unknown embedding error')
                logger.error(f"Query embedding failed: {exec_result.get('error')}")
                return {"next_state": "failed"}
                
        except Exception as e:
            logger.error(f"QueryEmbedderNode post error: {str(e)}")
            shared_store['embedding_error'] = f"Post-processing failed: {str(e)}"
            return {"next_state": "failed"}
    
