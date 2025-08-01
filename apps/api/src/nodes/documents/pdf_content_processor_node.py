"""
PDFContentProcessorNode for processing markdown content and generating PDF.

Split from pdf_generator_node.py to comply with PocketFlow 150-line limit.
Handles the exec phase of PDF generation using reportlab.
"""

import io
import logging
import re
from typing import Dict, Any
from datetime import datetime
from pocketflow import AsyncNode
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from ...utils.pdf_styles import PDFStyleUtils

logger = logging.getLogger(__name__)


class PDFContentProcessorNode(AsyncNode):
    """Processes markdown content and generates PDF using reportlab."""
    
    def __init__(self):
        super().__init__()
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Prepare for PDF content processing."""
        try:
            # Check that validation was successful
            if not shared_store.get('validated_data'):
                return {"error": "PDF validation failed - cannot proceed with content processing"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"PDFContentProcessorNode prep error: {str(e)}")
            return {"error": f"PDF content processing preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Convert markdown to PDF using reportlab."""
        try:
            validated_data = shared_store['validated_data']
            markdown_content = validated_data["markdown_content"]
            custom_filename = validated_data.get("filename")
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            if custom_filename:
                # Sanitize custom filename
                safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', custom_filename)
                if not safe_filename.endswith('.pdf'):
                    safe_filename += '.pdf'
                generated_filename = safe_filename
            else:
                generated_filename = f"theo-export-{timestamp}.pdf"
            
            # Create PDF buffer
            pdf_buffer = io.BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build PDF content
            story = []
            styles = PDFStyleUtils.create_styles()
            
            # Parse markdown and convert to PDF elements  
            story = self._convert_markdown_to_pdf(markdown_content, styles)
            
            # Build the PDF
            doc.build(story)
            
            # Get the PDF bytes
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            logger.info(f"PDF generation successful: {len(pdf_bytes)} bytes, filename: {generated_filename}")
            
            return {
                'success': True,
                'pdf_buffer': pdf_bytes,
                'pdf_size': len(pdf_bytes),
                'generated_filename': generated_filename
            }
            
        except Exception as e:
            error_msg = f"PDF content processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'pdf_buffer': b'',
                'pdf_size': 0,
                'generated_filename': ''
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store PDF processing results for downstream processing."""
        try:
            # Results are stored by the framework
            logger.info("PDF content processing completed")
            return {"next_state": "processed"}
            
        except Exception as e:
            logger.error(f"PDFContentProcessorNode post error: {str(e)}")
            return {"next_state": "failed"}
    
    def _convert_markdown_to_pdf(self, markdown_content: str, styles: dict) -> list:
        """Convert markdown content to PDF story elements."""
        story = []
        lines = markdown_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 12))
                continue
            
            # Headers
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('# ').strip()
                if text:
                    style_name = f'Heading{min(level, 3)}'
                    story.append(Paragraph(text, styles[style_name]))
                    story.append(Spacer(1, 12))
            # Lists
            elif line.startswith(('- ', '* ', '+ ')):
                item_text = line[2:].strip()
                story.append(Paragraph(f"• {item_text}", styles['Normal']))
            # Regular paragraphs
            else:
                formatted_text = PDFStyleUtils.process_inline_formatting(line)
                story.append(Paragraph(formatted_text, styles['Normal']))
                story.append(Spacer(1, 6))
        
        return story