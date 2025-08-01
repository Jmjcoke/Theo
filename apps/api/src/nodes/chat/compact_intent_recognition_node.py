"""CompactIntentRecognitionNode for classifying user input as new_query or format_request."""

from typing import Dict, Any
from pocketflow import AsyncNode
from ...utils.openai_client import get_openai_client
from ...utils.intent_patterns import IntentPatterns
import logging
import yaml

logger = logging.getLogger(__name__)


class CompactIntentRecognitionNode(AsyncNode):
    """Classifies user input intent using OpenAI GPT-4 with IntentPatterns utility."""
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.1):
        super().__init__(max_retries=3, wait=1)
        self.model = model
        self.temperature = temperature
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate user input for intent classification."""
        try:
            if 'message' not in shared_store:
                return {"error": "Missing required 'message' field"}
            
            message = shared_store['message']
            if not message or not isinstance(message, str):
                return {"error": "Message must be a non-empty string"}
            
            validated_message = message.strip()
            if not validated_message:
                return {"error": "Message cannot be empty after sanitization"}
            
            return {"success": True, "validated_message": validated_message}
            
        except KeyError as e:
            logger.error(f"CompactIntentRecognitionNode prep KeyError: {str(e)}")
            logger.error(f"Available keys in shared_store: {list(shared_store.keys())}")
            return {"error": f"Intent recognition preparation failed: missing key {str(e)}"}
        except Exception as e:
            logger.error(f"CompactIntentRecognitionNode prep error: {str(e)}")
            logger.error(f"Available keys in shared_store: {list(shared_store.keys())}")
            return {"error": f"Intent recognition preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> dict:
        """Classify user input intent using OpenAI GPT-4."""
        try:
            # Check if prep failed
            if not prep_result.get('success', False):
                return prep_result  # Return the error from prep
            
            message = prep_result['validated_message']
            
            # Try quick pattern-based classification first
            quick_result = IntentPatterns.quick_intent_classification(message)
            if IntentPatterns.is_high_confidence(quick_result['confidence']):
                return {
                    'success': True,
                    'intent': quick_result['intent'],
                    'confidence': quick_result['confidence'],
                    'method': quick_result['method']
                }
            
            # Fall back to LLM classification for ambiguous cases
            try:
                client = get_openai_client()
                prompt = IntentPatterns.build_intent_prompt(message)
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=self.temperature
                )
                
                response_text = response.choices[0].message.content.strip()
                try:
                    parsed = yaml.safe_load(response_text)
                    intent = parsed.get('intent', 'new_query')
                    confidence = parsed.get('confidence', 0.5)
                except (yaml.YAMLError, AttributeError):
                    intent = 'format_request' if 'format' in response_text.lower() else 'new_query'
                    confidence = 0.7
                
                # Validate intent
                if not IntentPatterns.validate_intent(intent):
                    intent = 'new_query'
                    confidence = 0.5
                
                return {
                    'success': True,
                    'intent': intent,
                    'confidence': float(confidence),
                    'method': 'llm_classification',
                    'model_used': self.model
                }
                
            except Exception as e:
                logger.warning(f"LLM classification failed: {str(e)}, using pattern fallback")
                # Use pattern-based fallback
                fallback_result = IntentPatterns.quick_intent_classification(message)
                return {
                    'success': True,
                    'intent': fallback_result['intent'],
                    'confidence': fallback_result['confidence'],
                    'method': 'pattern_fallback',
                    'llm_error': str(e)
                }
            
        except Exception as e:
            error_msg = f"Intent classification failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'intent': 'new_query',
                'confidence': 0.0
            }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> dict:
        """Store intent classification results in shared store."""
        try:
            # exec_result is now passed as a parameter
            
            if exec_result.get('success', False):
                shared_store['intent'] = exec_result['intent']
                shared_store['intent_confidence'] = exec_result['confidence']
                shared_store['intent_method'] = exec_result.get('method', 'unknown')
                shared_store['intent_model'] = exec_result.get('model_used', self.model)
                
                logger.info(f"Intent classified as '{exec_result['intent']}' with confidence {exec_result['confidence']}")
                return {"next_state": "classified"}
            else:
                shared_store['intent_error'] = exec_result.get('error', 'Unknown intent classification error')
                shared_store['intent'] = exec_result.get('intent', 'new_query')
                shared_store['intent_confidence'] = exec_result.get('confidence', 0.0)
                
                logger.error(f"Intent classification failed: {exec_result.get('error')}")
                return {"next_state": "failed"}
                
        except Exception as e:
            logger.error(f"CompactIntentRecognitionNode post error: {str(e)}")
            shared_store['intent_error'] = f"Intent post-processing failed: {str(e)}"
            shared_store['intent'] = 'new_query'
            shared_store['intent_confidence'] = 0.0
            return {"next_state": "failed"}