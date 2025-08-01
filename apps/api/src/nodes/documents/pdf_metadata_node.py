"""
PDFMetadataNode for storing PDF generation results and metadata.

Split from pdf_generator_node.py to comply with PocketFlow 150-line limit.
Handles the post phase of PDF generation result storage.
"""

import logging
from typing import Dict, Any
from pocketflow import AsyncNode

logger = logging.getLogger(__name__)


class PDFMetadataNode(AsyncNode):
    """Stores PDF generation results and metadata in shared store."""
    
    def __init__(self):
        super().__init__()
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Prepare for PDF metadata storage."""
        try:
            # Check that content processing was successful
            if not shared_store.get('pdf_buffer'):
                return {"error": "No PDF buffer available for metadata storage"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"PDFMetadataNode prep error: {str(e)}")
            return {"error": f"PDF metadata preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Process and validate PDF generation results."""
        try:
            # Get PDF generation results
            pdf_buffer = shared_store.get('pdf_buffer', b'')
            pdf_size = shared_store.get('pdf_size', 0)
            generated_filename = shared_store.get('generated_filename', '')
            
            # Validate results
            if not pdf_buffer:
                return {
                    'success': False,
                    'error': "PDF buffer is empty"
                }
            
            if pdf_size == 0:
                return {
                    'success': False,
                    'error': "PDF size is zero"
                }
            
            if not generated_filename:
                return {
                    'success': False,
                    'error': "Generated filename is empty"
                }
            
            # Create metadata summary
            metadata = {
                'pdf_size': pdf_size,
                'generated_filename': generated_filename,
                'content_type': 'application/pdf',
                'generation_status': 'completed',
                'has_content': len(pdf_buffer) > 0
            }
            
            logger.info(f"PDF metadata processed: {generated_filename}, {pdf_size} bytes")
            
            return {
                'success': True,
                'pdf_metadata': metadata
            }
            
        except Exception as e:
            error_msg = f"PDF metadata processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'pdf_metadata': {}
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store final PDF results and metadata in shared store."""
        try:
            # Get execution results
            exec_result = shared_store.get('exec_result', {})
            
            if exec_result.get('success', False):
                # Store PDF metadata
                shared_store['pdf_metadata'] = exec_result.get('pdf_metadata', {})
                
                # Log successful completion
                metadata = exec_result.get('pdf_metadata', {})
                filename = metadata.get('generated_filename', 'unknown')
                size = metadata.get('pdf_size', 0)
                
                logger.info(f"PDF generation completed successfully: {filename}, {size} bytes")
                
                return {"next_state": "completed"}
            else:
                # Handle failure
                error = exec_result.get('error', 'Unknown PDF metadata error')
                shared_store['pdf_error'] = error
                shared_store['pdf_metadata'] = {}
                
                logger.error(f"PDF metadata processing failed: {error}")
                return {"next_state": "failed"}
                
        except Exception as e:
            error_msg = f"PDF metadata post processing failed: {str(e)}"
            logger.error(error_msg)
            
            # Ensure clean state on error
            shared_store['pdf_error'] = error_msg
            shared_store['pdf_metadata'] = {}
            
            return {"next_state": "failed"}