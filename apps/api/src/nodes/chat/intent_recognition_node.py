"""
IntentRecognitionNode for classifying user input as new_query or format_request

Following PocketFlow AsyncNode pattern for LLM-based intent classification.
Determines whether user input requires RAG search or is a formatting command.
"""

from typing import Dict, Any
from pocketflow import AsyncNode
from ...utils.openai_client import get_openai_client
import logging
import yaml

logger = logging.getLogger(__name__)


class IntentRecognitionNode(AsyncNode):
    """Classifies user input intent using OpenAI GPT-4 following PocketFlow patterns"""
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.1):
        """Initialize the intent recognition node with configurable parameters"""
        super().__init__(max_retries=3, wait=1)
        self.model = model
        self.temperature = temperature
    
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate user input for intent classification and prepare execution data"""
        try:
            if 'message' not in shared_store:
                return {"error": "Missing required 'message' field"}
            
            message = shared_store['message']
            if not message or not isinstance(message, str):
                return {"error": "Message must be a non-empty string"}
            
            try:
                openai_client = get_openai_client()
            except ValueError as e:
                return {"error": f"OpenAI configuration error: {str(e)}"}
            
            validated_message = message.strip()
            if not validated_message:
                return {"error": "Message cannot be empty after sanitization"}
            
            # Return prepared data for exec_async
            return {
                "validated_message": validated_message,
                "openai_client": openai_client,
                "intent_model": self.model,
                "intent_temperature": self.temperature
            }
            
        except Exception as e:
            logger.error(f"IntentRecognitionNode prep error: {str(e)}")
            return {"error": f"Intent recognition preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: dict) -> Dict[str, Any]:
        """Classify user input intent using OpenAI GPT-4"""
        if "error" in prep_result:
            return {"success": False, "error": prep_result["error"]}
            
        try:
            # Use prep_result data instead of accessing shared_store
            client = prep_result.get('openai_client')
            message = prep_result.get('validated_message')
            model = prep_result.get('intent_model')
            temperature = prep_result.get('intent_temperature')
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": self._build_intent_prompt(message)}],
                max_tokens=100,
                temperature=temperature
            )
            
            response_text = response.choices[0].message.content.strip()
            try:
                parsed = yaml.safe_load(response_text)
                intent = parsed.get('intent', 'new_query')
                confidence = parsed.get('confidence', 0.5)
            except (yaml.YAMLError, AttributeError):
                intent = 'format_request' if 'format' in response_text.lower() else 'new_query'
                confidence = 0.7
            
            if intent not in ['new_query', 'format_request']:
                intent = 'new_query'
                confidence = 0.5
            
            return {
                "success": True,
                "intent": intent,
                "confidence": float(confidence),
                "model_used": model
            }
            
        except Exception as e:
            logger.error(f"IntentRecognitionNode exec error: {str(e)}")
            return {"success": False, "error": f"Intent classification failed: {str(e)}"}
    
    def _build_intent_prompt(self, message: str) -> str:
        """Build prompt for intent classification"""
        return f"""Classify the user's input as either a new query requiring information search or a formatting command.

User input: "{message}"

Return YAML format:
intent: new_query|format_request
confidence: 0.0-1.0

Examples:
- "What is biblical hermeneutics?" → intent: new_query
- "Format the previous response as bullet points" → intent: format_request
- "Make that into a table" → intent: format_request
- "Explain John 3:16" → intent: new_query

Classification:"""
    
    async def exec_fallback_async(self, prep_result: dict, exc: Exception) -> Dict[str, Any]:
        """Fallback for classification failures after retries"""
        logger.error(f"IntentRecognitionNode failed after retries: {str(exc)}")
        return {
            "success": False,
            "error": "Intent classification failed after multiple retries",
            "retry_count": self.max_retries,
            "intent": "new_query",
            "confidence": 0.0
        }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: dict, exec_result: Dict[str, Any]) -> dict:
        """Update shared store with intent classification results"""
        try:
            if exec_result.get('success', False):
                shared_store['intent'] = exec_result['intent']
                shared_store['intent_confidence'] = exec_result['confidence']
                shared_store['intent_model'] = exec_result.get('model_used', self.model)
                logger.info(f"Intent classified as '{exec_result['intent']}' with confidence {exec_result['confidence']}")
                return {"next_state": "success"}
            else:
                shared_store['intent_error'] = exec_result.get('error', 'Unknown intent classification error')
                shared_store['intent'] = exec_result.get('intent', 'new_query')
                shared_store['intent_confidence'] = exec_result.get('confidence', 0.0)
                logger.error(f"Intent classification failed: {exec_result.get('error')}")
                return {"next_state": "failed"}
                
        except Exception as e:
            logger.error(f"IntentRecognitionNode post error: {str(e)}")
            shared_store['intent_error'] = f"Intent post-processing failed: {str(e)}"
            shared_store['intent'] = 'new_query'
            shared_store['intent_confidence'] = 0.0
            return {"next_state": "failed"}
    
    
