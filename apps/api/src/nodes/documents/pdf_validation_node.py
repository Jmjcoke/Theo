"""
PDFValidationNode for validating markdown content before PDF generation.

Split from pdf_generator_node.py to comply with PocketFlow 150-line limit.
Handles the prep phase of PDF generation validation.
"""

import logging
from typing import Dict, Any
from pocketflow import AsyncNode

logger = logging.getLogger(__name__)


class PDFValidationNode(AsyncNode):
    """Validates markdown content for PDF generation."""
    
    def __init__(self):
        super().__init__()
        self.max_content_length = 1_000_000  # 1MB limit
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Prepare for markdown content validation."""
        try:
            # Check that required fields exist
            if 'markdown_content' not in shared_store:
                return {"error": "Missing required 'markdown_content' field for PDF generation"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"PDFValidationNode prep error: {str(e)}")
            return {"error": f"PDF validation preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate markdown content and prepare PDF generation parameters."""
        try:
            # Validate required fields
            required_keys = ["markdown_content"]
            missing_keys = [key for key in required_keys if key not in shared_store]
            
            if missing_keys:
                return {
                    'success': False,
                    'error': f"Missing required keys: {missing_keys}"
                }
            
            markdown_content = shared_store["markdown_content"]
            
            # Validate content type
            if not isinstance(markdown_content, str):
                return {
                    'success': False,
                    'error': "markdown_content must be a string"
                }
            
            # Validate content length
            if len(markdown_content) > self.max_content_length:
                return {
                    'success': False,
                    'error': f"Content too large: {len(markdown_content)} bytes exceeds {self.max_content_length}"
                }
            
            # Validate content not empty
            if not markdown_content.strip():
                return {
                    'success': False,
                    'error': "Empty markdown content provided"
                }
            
            # Prepare validated data
            validated_data = {
                "markdown_content": markdown_content,
                "filename": shared_store.get("filename")
            }
            
            logger.info(f"PDF validation successful for content: {len(markdown_content)} bytes")
            
            return {
                'success': True,
                'validated_data': validated_data
            }
            
        except Exception as e:
            error_msg = f"PDF validation failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store validation results for downstream processing."""
        try:
            # Validation results are stored by the framework
            logger.info("PDF validation completed")
            return {"next_state": "validated"}
            
        except Exception as e:
            logger.error(f"PDFValidationNode post error: {str(e)}")
            return {"next_state": "failed"}