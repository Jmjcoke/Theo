"""
ContentFormatterNode for applying LLM-based document formatting.

Split from structured_formatting_node.py to comply with PocketFlow 150-line limit.
Handles the exec phase of structured document formatting using OpenAI.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
from pocketflow import AsyncNode
from src.utils.openai_client import get_openai_client
from src.utils.document_templates import DocumentTemplateUtils

logger = logging.getLogger(__name__)


class ContentFormatterNode(AsyncNode):
    """Applies LLM-based formatting to document content using templates."""
    
    def __init__(self, model="gpt-4o", temperature=0.3):
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.client = get_openai_client()
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Prepare for content formatting execution."""
        try:
            # Check that validation was successful
            if not shared_store.get('validation_result', {}).get('is_valid', False):
                return {"error": "Template validation failed - cannot proceed with formatting"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"ContentFormatterNode prep error: {str(e)}")
            return {"error": f"Formatting preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute structured formatting using OpenAI and the validated template."""
        start_time = time.time()
        
        try:
            # Get validated data from shared store
            validation_result = shared_store['validation_result']
            content = shared_store['content']
            template_id = shared_store['templateId']
            formatting_options = shared_store['formattingOptions']
            context = shared_store.get('context', '')
            
            template = validation_result['template']
            
            # Build formatting prompt
            prompt = self._build_formatting_prompt(template, content, formatting_options, context)
            
            # Call OpenAI for formatting
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=self.temperature
            )
            
            formatted_content = response.choices[0].message.content.strip()
            processing_time = time.time() - start_time
            
            # Get applied formatting details
            applied_formatting = self._get_applied_formatting(template, formatting_options)
            
            return {
                'success': True,
                'formatted_content': formatted_content,
                'original_content': content,
                'template_used': template,
                'applied_formatting': applied_formatting,
                'processing_time': processing_time,
                'model_used': self.model,
                'token_usage': response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            error_msg = f"Content formatting failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'formatted_content': content,  # Return original content as fallback
                'processing_time': time.time() - start_time
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store formatting results for downstream processing."""
        try:
            # Results are stored in shared_store by the framework
            logger.info("Content formatting completed")
            return {"next_state": "formatted"}
            
        except Exception as e:
            logger.error(f"ContentFormatterNode post error: {str(e)}")
            return {"next_state": "failed"}
    
    def _build_formatting_prompt(self, template: Dict[str, Any], content: str, 
                                formatting_options: Dict[str, Any], context: str) -> str:
        """Build prompt for structured formatting using the template."""
        template_name = template.get('name', 'Document')
        instructions = template.get('instructions', '')
        context_text = f"\n\nContext: {context}" if context else ""
        
        return f"""Format as {template_name}:

{instructions}

Content: {content}{context_text}"""
    
    def _get_applied_formatting(self, template: Dict[str, Any], formatting_options: Dict[str, Any]) -> List[str]:
        """Extract and describe applied formatting options."""
        category = template.get('category', '')
        applied = [f"{category.title()} format applied"]
        
        for key, value in formatting_options.items():
            if value:
                applied.append(f"{key}: {value}")
        
        return applied[:3]  # Limit to 3 items