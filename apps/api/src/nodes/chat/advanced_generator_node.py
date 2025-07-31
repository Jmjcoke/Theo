"""AdvancedGeneratorNode for hermeneutics-guided theological AI responses"""

from typing import Dict, Any, List
from pocketflow import AsyncNode
from ...utils.openai_client import get_openai_client
from ...utils.hermeneutics_config import HermeneuticsConfig
from ...utils.citation_utils import calculate_confidence
from ...utils.prompt_utils import build_source_info, build_hermeneutics_prompt
import logging
import time

logger = logging.getLogger(__name__)


class AdvancedGeneratorNode(AsyncNode):
    """Generates hermeneutics-guided theological responses"""
    
    def __init__(self, model: str = "gpt-4", max_tokens: int = 1500, temperature: float = 0.3):
        super().__init__(max_retries=3, wait=2)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.hermeneutics_config = HermeneuticsConfig()
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate query, context, and hermeneutics configuration"""
        try:
            if 'query' not in shared_store or not shared_store['query']:
                raise ValueError("Missing user query")
            
            # Get re-ranked or search results
            search_results = shared_store.get('re_ranked_results') or shared_store.get('search_results')
            if not search_results or not isinstance(search_results, list):
                raise ValueError("Missing or invalid search results")
            
            # Validate OpenAI client and hermeneutics prompt
            try:
                openai_client = get_openai_client()
                hermeneutics_prompt = self.hermeneutics_config.get_system_prompt()
                if not hermeneutics_prompt:
                    raise ValueError("Failed to load hermeneutics prompt")
            except Exception as e:
                raise ValueError(f"Configuration error: {str(e)}")
            
            # Return validated data for exec_async
            return {
                'validated_query': shared_store['query'].strip(),
                'search_results': search_results,
                'openai_client': openai_client,
                'hermeneutics_prompt': hermeneutics_prompt,
                'model': self.model,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'hermeneutics_version': self.hermeneutics_config.get_version()
            }
            
        except Exception as e:
            logger.error(f"AdvancedGeneratorNode prep error: {str(e)}")
            raise ValueError(f"Advanced generation preparation failed: {str(e)}")
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hermeneutics-guided theological response"""
        try:
            start_time = time.time()
            
            # Use prep_result data instead of shared_store hack
            hermeneutics_prompt = prep_result['hermeneutics_prompt']
            validated_results = prep_result['search_results']
            validated_query = prep_result['validated_query']
            openai_client = prep_result['openai_client']
            model = prep_result['model']
            max_tokens = prep_result['max_tokens']
            temperature = prep_result['temperature']
            hermeneutics_version = prep_result['hermeneutics_version']
            
            # Compose and generate response
            final_prompt = build_hermeneutics_prompt(
                hermeneutics_prompt,
                validated_results,
                validated_query
            )
            
            response = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": final_prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            generated_answer = response.choices[0].message.content
            search_results = validated_results
            source_info = build_source_info(search_results)
            
            return {
                "success": True,
                "generated_answer": generated_answer,
                "confidence": calculate_confidence(search_results, generated_answer),
                "source_info": source_info,
                "model_used": model,
                "hermeneutics_version": hermeneutics_version,
                "context_sources_count": len(source_info),
                "generation_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"AdvancedGeneratorNode exec error: {str(e)}")
            return {"success": False, "error": f"Hermeneutics generation failed: {str(e)}"}
    
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """Update shared store with hermeneutics generation results"""
        try:
            if exec_result.get('success', False):
                shared_store.update({
                    'generated_answer': exec_result['generated_answer'],
                    'confidence': exec_result['confidence'],
                    'source_info': exec_result['source_info'],
                    'generation_model': exec_result.get('model_used', prep_result.get('model', self.model)),
                    'hermeneutics_metadata': {
                        'version': exec_result.get('hermeneutics_version'),
                        'generation_time': exec_result.get('generation_time'),
                        'hermeneutics_applied': True
                    },
                    'context_sources_count': exec_result.get('context_sources_count', 0)
                })
                logger.info(f"Hermeneutics answer generated with {exec_result.get('context_sources_count', 0)} sources")
                return "default"
            else:
                shared_store['generation_error'] = exec_result.get('error', 'Unknown hermeneutics error')
                logger.error(f"Hermeneutics generation failed: {exec_result.get('error')}")
                return "failed"
        except Exception as e:
            logger.error(f"AdvancedGeneratorNode post error: {str(e)}")
            shared_store['generation_error'] = f"Post-processing failed: {str(e)}"
            return "failed"
    
    
