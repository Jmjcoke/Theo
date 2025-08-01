"""
TemplateValidationNode for validating formatting requests and templates.

Split from structured_formatting_node.py to comply with PocketFlow 150-line limit.
Handles the prep phase of structured document formatting.
"""

import logging
from typing import Dict, Any
from pocketflow import AsyncNode
from src.utils.document_templates import DocumentTemplateUtils

logger = logging.getLogger(__name__)


class TemplateValidationNode(AsyncNode):
    """Validates formatting request and prepares template data."""
    
    def __init__(self):
        super().__init__()
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate inputs and prepare for template processing."""
        try:
            # Validate required fields
            required_fields = ['content', 'templateId', 'formattingOptions']
            for field in required_fields:
                if field not in shared_store:
                    return {"error": f"Missing required field: {field}"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"TemplateValidationNode prep error: {str(e)}")
            return {"error": f"Preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute template validation and content validation."""
        try:
            # Get inputs
            content = shared_store['content']
            template_id = shared_store['templateId']
            formatting_options = shared_store['formattingOptions']
            
            validation_errors = []
            
            # Validate template exists
            if not DocumentTemplateUtils.validate_template_id(template_id):
                validation_errors.append(f"Unknown template: {template_id}")
            
            # Validate content
            if not content or len(content.strip()) == 0:
                validation_errors.append("Content cannot be empty")
            
            if len(content) > 50000:  # 50KB limit
                validation_errors.append("Content too long (max 50KB)")
            
            # Validate formatting options structure
            if not isinstance(formatting_options, dict):
                validation_errors.append("Formatting options must be a dictionary")
            
            # Check for required template sections if specified
            if not validation_errors:
                template = DocumentTemplateUtils.get_template(template_id)
                required_sections = DocumentTemplateUtils.get_required_sections(template_id)
                
                # Store validation results
                validation_result = {
                    'is_valid': len(validation_errors) == 0,
                    'errors': validation_errors,
                    'template': template,
                    'required_sections': required_sections,
                    'template_category': DocumentTemplateUtils.get_template_category(template_id),
                    'template_instructions': DocumentTemplateUtils.get_template_instructions(template_id)
                }
            else:
                validation_result = {
                    'is_valid': False,
                    'errors': validation_errors,
                    'template': None,
                    'required_sections': [],
                    'template_category': '',
                    'template_instructions': ''
                }
            
            return {
                'success': validation_result['is_valid'],
                'validation_result': validation_result,
                'content': content,
                'template_id': template_id,
                'formatting_options': formatting_options
            }
            
        except Exception as e:
            error_msg = f"Template validation failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'validation_result': {
                    'is_valid': False,
                    'errors': [error_msg],
                    'template': None,
                    'required_sections': [],
                    'template_category': '',
                    'template_instructions': ''
                }
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store validation results in shared store for downstream nodes."""
        try:
            # Validation results are already stored in shared_store by upstream processing
            # This node primarily validates and passes data forward
            logger.info("Template validation completed")
            return {"next_state": "validated"}
            
        except Exception as e:
            logger.error(f"TemplateValidationNode post error: {str(e)}")
            return {"next_state": "failed"}