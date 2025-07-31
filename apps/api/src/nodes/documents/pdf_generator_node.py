"""
PDF Generator Node for converting markdown content to PDF files.

This node generates PDF files from markdown content using reportlab library
following PocketFlow AsyncNode patterns for I/O operations.

Cookbook Reference: pocketflow-external-service
"""
import io
from typing import Dict, Any, Optional
from datetime import datetime
from pocketflow import AsyncNode
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, blue
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import re


class PDFGeneratorNode(AsyncNode):
    """
    Generates PDF files from markdown content using reportlab.
    
    Converts markdown text to formatted PDF with proper styling
    for headers, paragraphs, lists, and basic formatting.
    
    Input (shared_store):
        - markdown_content: str - The markdown content to convert
        - filename: Optional[str] - Custom filename for the PDF
        
    Output (shared_store):
        - pdf_buffer: bytes - Generated PDF as byte buffer
        - pdf_size: int - Size of generated PDF in bytes
        - generated_filename: str - Final filename used
    """
    
    def __init__(self):
        super().__init__()
        self.max_content_length = 1_000_000  # 1MB limit
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate markdown content and prepare for PDF generation."""
        required_keys = ["markdown_content"]
        missing_keys = [key for key in required_keys if key not in shared_store]
        
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        markdown_content = shared_store["markdown_content"]
        if not isinstance(markdown_content, str):
            raise ValueError("markdown_content must be a string")
        
        if len(markdown_content) > self.max_content_length:
            raise ValueError(f"Content too large: {len(markdown_content)} bytes exceeds {self.max_content_length}")
        
        if not markdown_content.strip():
            raise ValueError("Empty markdown content provided")
        
        return {
            "markdown_content": markdown_content,
            "filename": shared_store.get("filename")
        }
    
    async def exec_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert markdown to PDF using reportlab."""
        markdown_content = data["markdown_content"]
        custom_filename = data.get("filename")
        
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
        styles = self._create_styles()
        
        # Parse markdown and convert to PDF elements
        lines = markdown_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                story.append(Spacer(1, 12))
                i += 1
                continue
            
            # Handle headers
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('# ').strip()
                if text:
                    style_name = f'Heading{min(level, 3)}'
                    story.append(Paragraph(text, styles[style_name]))
                    story.append(Spacer(1, 12))
            
            # Handle lists
            elif line.startswith(('- ', '* ', '+ ')):
                list_items = []
                while i < len(lines) and lines[i].strip().startswith(('- ', '* ', '+ ')):
                    item_text = lines[i].strip()[2:].strip()
                    if item_text:
                        list_items.append(item_text)
                    i += 1
                i -= 1  # Adjust for the outer loop increment
                
                for item in list_items:
                    story.append(Paragraph(f"• {item}", styles['Normal']))
                story.append(Spacer(1, 6))
            
            # Handle numbered lists
            elif re.match(r'^\d+\.\s', line):
                list_items = []
                while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                    item_text = re.sub(r'^\d+\.\s*', '', lines[i].strip())
                    if item_text:
                        list_items.append(item_text)
                    i += 1
                i -= 1  # Adjust for the outer loop increment
                
                for idx, item in enumerate(list_items, 1):
                    story.append(Paragraph(f"{idx}. {item}", styles['Normal']))
                story.append(Spacer(1, 6))
            
            # Handle regular paragraphs
            else:
                # Process inline formatting
                formatted_text = self._process_inline_formatting(line)
                story.append(Paragraph(formatted_text, styles['Normal']))
                story.append(Spacer(1, 6))
            
            i += 1
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        return {
            "pdf_buffer": pdf_bytes,
            "pdf_size": len(pdf_bytes),
            "generated_filename": generated_filename
        }
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for PDF generation."""
        styles = getSampleStyleSheet()
        
        # Customize existing styles
        styles['Normal'].fontSize = 11
        styles['Normal'].leading = 14
        styles['Normal'].spaceAfter = 6
        
        # Override existing heading styles or use them directly
        if 'Heading1' in styles:
            styles['Heading1'].fontSize = 18
            styles['Heading1'].leading = 22
            styles['Heading1'].spaceBefore = 12
            styles['Heading1'].spaceAfter = 12
        
        if 'Heading2' in styles:
            styles['Heading2'].fontSize = 16
            styles['Heading2'].leading = 20
            styles['Heading2'].spaceBefore = 10
            styles['Heading2'].spaceAfter = 10
        
        if 'Heading3' in styles:
            styles['Heading3'].fontSize = 14
            styles['Heading3'].leading = 18
            styles['Heading3'].spaceBefore = 8
            styles['Heading3'].spaceAfter = 8
        
        return styles
    
    def _process_inline_formatting(self, text: str) -> str:
        """Process basic markdown inline formatting."""
        # Bold (**text**)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Italic (*text*)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Code (`text`)
        text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
        
        # Links [text](url) - convert to blue underlined text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'<u><font color="blue">\1</font></u>', text)
        
        return text
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> None:
        """Store PDF buffer and metadata in shared store."""
        shared_store["pdf_buffer"] = exec_result["pdf_buffer"]
        shared_store["pdf_size"] = exec_result["pdf_size"]
        shared_store["generated_filename"] = exec_result["generated_filename"]