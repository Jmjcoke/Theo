"""CompactReRankerNode for improving contextual relevance using LLM-based theological re-ranking."""

from typing import Dict, Any
from pocketflow import AsyncNode
from ...utils.openai_client import get_openai_client
import logging
import json

logger = logging.getLogger(__name__)


class CompactReRankerNode(AsyncNode):
    """Re-ranks search results using LLM theological relevance scoring."""
    
    def __init__(self, model: str = "gpt-4", top_k: int = 5, temperature: float = 0.1):
        super().__init__(max_retries=3, wait=1)
        self.model = model
        self.top_k = top_k
        self.temperature = temperature
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate query and search results from shared store."""
        try:
            query = shared_store.get('query') or shared_store.get('user_query')
            if not query:
                return {"error": "Missing query or user_query field"}
            
            if 'search_results' not in shared_store or not isinstance(shared_store['search_results'], list):
                return {"error": "Missing or invalid search_results"}
            
            search_results = shared_store['search_results']
            for i, result in enumerate(search_results):
                if not isinstance(result, dict) or 'content' not in result:
                    return {"error": f"Invalid search result {i}: missing content"}
            
            return {
                "success": True,
                "query": query,
                "search_results": search_results
            }
            
        except Exception as e:
            logger.error(f"CompactReRankerNode prep error: {str(e)}")
            return {"error": f"Re-ranking preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> dict:
        """Execute LLM-based theological re-ranking."""
        try:
            # Check if prep failed
            if not prep_result.get('success', False):
                return prep_result  # Return the error from prep
            
            query = prep_result['query']
            search_results = prep_result['search_results']
            
            if len(search_results) <= 1:
                return {
                    'success': True,
                    'reranked_results': search_results[:self.top_k],
                    'original_count': len(search_results),
                    'reranked_count': len(search_results)
                }
            
            # Create ranking prompt
            ranking_prompt = self._build_ranking_prompt(query, search_results)
            
            # Get LLM ranking
            client = get_openai_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": ranking_prompt}],
                temperature=self.temperature,
                max_tokens=500
            )
            
            # Parse ranking response
            ranking_response = response.choices[0].message.content.strip()
            reranked_results = self._parse_ranking_response(ranking_response, search_results)
            
            return {
                'success': True,
                'reranked_results': reranked_results[:self.top_k],
                'original_count': len(search_results),
                'reranked_count': len(reranked_results),
                'ranking_method': 'llm_theological'
            }
            
        except Exception as e:
            error_msg = f"Re-ranking execution failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'reranked_results': search_results[:self.top_k] if search_results else [],
                'original_count': len(search_results) if search_results else 0,
                'reranked_count': 0
            }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> dict:
        """Store re-ranking results in shared store."""
        try:
            
            if exec_result.get('success', False):
                shared_store['reranked_results'] = exec_result['reranked_results']
                shared_store['search_results'] = exec_result['reranked_results']  # Replace original
                shared_store['reranking_metadata'] = {
                    'original_count': exec_result.get('original_count', 0),
                    'reranked_count': exec_result.get('reranked_count', 0),
                    'ranking_method': exec_result.get('ranking_method', 'unknown')
                }
                
                return {"next_state": "reranked"}
            else:
                shared_store['reranking_error'] = exec_result.get('error', 'Unknown re-ranking error')
                shared_store['reranked_results'] = exec_result.get('reranked_results', [])
                return {"next_state": "failed"}
        except Exception as e:
            logger.error(f"CompactReRankerNode post error: {str(e)}")
            return {"next_state": "failed"}
    
    def _build_ranking_prompt(self, query: str, results: list) -> str:
        """Build ranking prompt for LLM."""
        results_text = ""
        for i, result in enumerate(results[:10]):
            content = result.get('content', '')[:300]
            results_text += f"{i+1}. {content}\n\n"
        return f'Rank these by relevance to "{query}":\n{results_text}\nReturn numbers only: Example: 3,1,5,2,4'
    
    def _parse_ranking_response(self, response: str, original_results: list) -> list:
        """Parse LLM ranking response and reorder results."""
        try:
            numbers = []
            for part in response.replace(' ', '').split(','):
                try:
                    num = int(part.strip())
                    if 1 <= num <= len(original_results):
                        numbers.append(num - 1)
                except ValueError:
                    continue
            
            reranked = []
            used_indices = set()
            for idx in numbers:
                if idx not in used_indices:
                    reranked.append(original_results[idx])
                    used_indices.add(idx)
            for idx, result in enumerate(original_results):
                if idx not in used_indices:
                    reranked.append(result)
            return reranked
        except Exception: return original_results