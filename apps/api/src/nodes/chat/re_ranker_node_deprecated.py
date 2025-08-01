"""ReRankerNode for improving contextual relevance using LLM-based theological re-ranking"""

from typing import Dict, Any
from pocketflow import AsyncNode
from ...utils.openai_client import get_openai_client
import logging
import json

logger = logging.getLogger(__name__)


class ReRankerNode(AsyncNode):
    """Re-ranks search results using LLM theological relevance scoring"""
    
    def __init__(self, model: str = "gpt-4", top_k: int = 5, temperature: float = 0.1):
        super().__init__(max_retries=3, wait=1)
        self.model = model
        self.top_k = top_k
        self.temperature = temperature
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate query and search results from shared store"""
        try:
            # Look for query in either 'query' or 'user_query' fields
            query = shared_store.get('query') or shared_store.get('user_query')
            if not query:
                raise ValueError("Missing query or user_query field")
            
            if 'search_results' not in shared_store or not isinstance(shared_store['search_results'], list):
                raise ValueError("Missing or invalid search_results")
            
            search_results = shared_store['search_results']
            for i, result in enumerate(search_results):
                if not isinstance(result, dict) or 'content' not in result:
                    raise ValueError(f"Invalid search result {i}: missing content")
            
            # Return validated data for exec_async
            return {
                'validated_query': query,
                'search_results': search_results,
                'model': self.model,
                'temperature': self.temperature,
                'top_k': self.top_k,
                'timeout': 15  # Configurable timeout instead of hardcoded 30s
            }
            
        except Exception as e:
            logger.error(f"ReRankerNode prep error: {str(e)}")
            raise ValueError(f"Re-ranking preparation failed: {str(e)}")
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM-based re-ranking of search results"""
        try:
            import time
            start_time = time.time()
            
            # Use prep_result data instead of shared_store hack
            user_query = prep_result['validated_query']
            search_results = prep_result['search_results']
            model = prep_result['model']
            temperature = prep_result['temperature']
            top_k = prep_result['top_k']
            timeout = prep_result['timeout']
            
            if not search_results:
                return {"success": True, "re_ranked_results": [], "original_count": 0}
            
            scored_results = []
            client = get_openai_client()
            # Use the comprehensive theological prompt from Dev Notes
            prompt_template = """You are a theological AI assistant specializing in biblical and doctrinal analysis.

Query: "{query}"

Evaluate the relevance of this document chunk to the query for theological research:
Chunk: "{chunk}"

Consider:
- Direct scriptural relevance
- Theological doctrinal connection
- Historical/contextual importance
- Hermeneutical significance

Provide a relevance score from 0.0 to 1.0 where:
- 1.0 = Directly answers the query with high theological precision
- 0.7-0.9 = Strong theological relevance with good supporting context
- 0.4-0.6 = Moderate relevance with useful background information
- 0.1-0.3 = Tangentially related theological content
- 0.0 = No meaningful theological relevance

Respond with only a JSON object: {{"score": 0.0, "reasoning": "Brief explanation"}}"""
            
            for result in search_results:
                try:
                    prompt = prompt_template.format(
                        query=user_query, chunk=result.get('content', '')[:1000]
                    )
                    response = client.chat.completions.create(
                        model=model, messages=[{"role": "user", "content": prompt}],
                        temperature=temperature, max_tokens=100, timeout=timeout
                    )
                    score_data = json.loads(response.choices[0].message.content.strip())
                    raw_score = float(score_data.get('score', 0.0))
                    # Clamp score to valid range [0.0, 1.0]
                    clamped_score = max(0.0, min(1.0, raw_score))
                    
                    updated_result = result.copy()
                    updated_result['llm_relevance'] = clamped_score
                    updated_result['re_ranking_reasoning'] = score_data.get('reasoning', '')
                    scored_results.append(updated_result)
                except Exception as chunk_error:
                    logger.warning(f"Failed to re-rank chunk {result.get('document_id', 'unknown')}: {str(chunk_error)}")
                    fallback_result = result.copy()
                    fallback_result['llm_relevance'] = result.get('relevance', 0.0)
                    fallback_result['re_ranking_reasoning'] = "Re-ranking failed, using original score"
                    scored_results.append(fallback_result)
            
            re_ranked_results = sorted(scored_results, key=lambda x: x.get('llm_relevance', 0.0), reverse=True)
            top_results = re_ranked_results[:top_k]
            
            # Add performance metrics
            end_time = time.time()
            processing_time = end_time - start_time
            logger.info(f"Re-ranking completed in {processing_time:.2f}s for {len(search_results)} chunks")
            
            return {
                "success": True, 
                "re_ranked_results": top_results, 
                "original_count": len(search_results),
                "processing_time": processing_time
            }
            
        except Exception as e:
            return {"success": False, "error": f"Re-ranking failed: {str(e)}"}
    
    async def exec_fallback_async(self, prep_result: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        """Fallback: return original search order when re-ranking fails"""
        logger.error(f"ReRankerNode failed after retries: {str(exc)}")
        
        # Use prep_result data instead of shared_store hack
        original_results = prep_result.get('search_results', [])
        top_k = prep_result.get('top_k', self.top_k)
        return {"success": True, "re_ranked_results": original_results[:top_k], 
                "fallback_used": True, "original_count": len(original_results)}
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """Update shared store with re-ranked results"""
        try:
            if exec_result.get('success', False):
                shared_store['re_ranked_results'] = exec_result['re_ranked_results']
                shared_store['re_ranking_metadata'] = {"model": self.model, "top_k": self.top_k}
                if exec_result.get('fallback_used'):
                    logger.warning("Re-ranking fallback used")
                return "default"
            else:
                shared_store['re_ranking_error'] = exec_result.get('error', 'Unknown error')
                return "failed"
        except Exception as e:
            shared_store['re_ranking_error'] = f"Post-processing failed: {str(e)}"
            return "failed"
    
    
