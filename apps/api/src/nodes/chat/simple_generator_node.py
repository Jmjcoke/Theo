"""
SimpleGeneratorNode for generating answers using OpenAI GPT-4
Following PocketFlow AsyncNode pattern for OpenAI API integration.
"""

from typing import Dict, Any, List
from pocketflow import AsyncNode
from ...utils.openai_client import get_openai_client
from ...utils.citation_utils import calculate_confidence
from ...utils.prompt_utils import build_context_prompt, build_source_info
import logging
import time

logger = logging.getLogger(__name__)


class SimpleGeneratorNode(AsyncNode):
    """Generates answers using OpenAI GPT-4 with retrieved context following PocketFlow patterns"""
    
    def __init__(self, model: str = "gpt-4", max_tokens: int = 1000, temperature: float = 0.7):
        """Initialize the generator node with configurable parameters"""
        super().__init__(max_retries=3, wait=2)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> bool:
        """Validate query and search results for answer generation"""
        try:
            # Check for required query
            if 'query' not in shared_store:
                shared_store['error'] = "Missing required 'query' field"
                return False
            
            query = shared_store['query']
            if not query or not isinstance(query, str):
                shared_store['error'] = "Query must be a non-empty string"
                return False
            
            # Check for search results (prioritize re-ranked results)
            if 're_ranked_results' in shared_store:
                search_results = shared_store['re_ranked_results']
            elif 'search_results' in shared_store:
                search_results = shared_store['search_results']
            else:
                shared_store['error'] = "Missing required search results"
                return False
            if not isinstance(search_results, list):
                shared_store['error'] = "Search results must be a list"
                return False
            
            # Validate OpenAI client availability
            try:
                client = get_openai_client()
                shared_store['openai_client'] = client
            except ValueError as e:
                shared_store['error'] = f"OpenAI configuration error: {str(e)}"
                return False
            
            # Store validated data
            shared_store['validated_query'] = query.strip()
            shared_store['validated_results'] = search_results
            return True
            
        except Exception as e:
            logger.error(f"SimpleGeneratorNode prep error: {str(e)}")
            shared_store['error'] = f"Generation preparation failed: {str(e)}"
            return False
    
    async def exec_async(self, prep_result: bool) -> Dict[str, Any]:
        """Generate answer using OpenAI GPT-4"""
        if not prep_result:
            return {"success": False, "error": "Preparation failed"}
        
        try:
            # Get shared store reference
            shared_store = getattr(self, '_current_shared_store', {})
            client = shared_store.get('openai_client')
            query = shared_store.get('validated_query')
            # Use re-ranked results if available, otherwise use search results
            search_results = shared_store.get('re_ranked_results', shared_store.get('search_results', []))
            
            # Build prompt and source info using utilities
            prompt = build_context_prompt(query, search_results)
            source_info = build_source_info(search_results)
            
            # Generate response using OpenAI
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            generated_answer = response.choices[0].message.content
            
            # Calculate confidence based on context quality and relevance
            confidence = calculate_confidence(search_results, generated_answer)
            
            return {
                "success": True,
                "generated_answer": generated_answer,
                "confidence": confidence,
                "source_info": source_info,
                "model_used": self.model,
                "context_sources_count": len(source_info)
            }
            
        except Exception as e:
            logger.error(f"SimpleGeneratorNode exec error: {str(e)}")
            return {"success": False, "error": f"Answer generation failed: {str(e)}"}
    
    async def exec_fallback_async(self, prep_result: bool, exc: Exception) -> Dict[str, Any]:
        """Fallback for generation failures after retries"""
        logger.error(f"SimpleGeneratorNode failed after retries: {str(exc)}")
        return {
            "success": False,
            "error": "Answer generation failed after multiple retries",
            "retry_count": self.max_retries
        }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: bool, exec_result: Dict[str, Any]) -> str:
        """Update shared store with generation results"""
        try:
            if exec_result.get('success', False):
                # Store generation results in shared store
                shared_store['generated_answer'] = exec_result['generated_answer']
                shared_store['confidence'] = exec_result['confidence']
                shared_store['source_info'] = exec_result['source_info']
                shared_store['generation_model'] = exec_result.get('model_used', self.model)
                shared_store['context_sources_count'] = exec_result.get('context_sources_count', 0)
                
                logger.info(f"Answer generated successfully with {exec_result.get('context_sources_count', 0)} sources")
                return "success"
            else:
                # Store error information
                shared_store['generation_error'] = exec_result.get('error', 'Unknown generation error')
                logger.error(f"Answer generation failed: {exec_result.get('error')}")
                return "failed"
                
        except Exception as e:
            logger.error(f"SimpleGeneratorNode post error: {str(e)}")
            shared_store['generation_error'] = f"Post-processing failed: {str(e)}"
            return "failed"
    
    
    async def _run_async(self, shared_store: Dict[str, Any]) -> str:
        """Override to store shared_store reference for exec_async"""
        self._current_shared_store = shared_store
        return await super()._run_async(shared_store)