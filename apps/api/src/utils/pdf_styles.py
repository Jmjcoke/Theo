"""
PDF Styles Utility

Centralized PDF styling and formatting utilities for document generation.
Extracted from pdf_generator_node.py to comply with PocketFlow 150-line limit.
"""

import re
from typing import Dict, Any
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, blue
from reportlab.lib.units import inch


class PDFStyleUtils:
    """Utility class for PDF styling and formatting operations"""
    
    @staticmethod
    def create_styles() -> Dict[str, ParagraphStyle]:
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
    
    @staticmethod
    def process_inline_formatting(text: str) -> str:
        """Process basic markdown inline formatting for PDF output."""
        # Bold (**text**)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Italic (*text*)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Code (`text`)
        text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
        
        # Links [text](url) - convert to blue underlined text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'<u><font color="blue">\1</font></u>', text)
        
        return text
    
    @staticmethod
    def get_default_page_config() -> Dict[str, Any]:
        """Get default page configuration for PDF documents."""
        return {
            'page_size': 'A4',
            'margins': {
                'top': 0.75 * inch,
                'bottom': 0.75 * inch,
                'left': 0.75 * inch,
                'right': 0.75 * inch
            },
            'title_font_size': 18,
            'heading1_font_size': 16,
            'heading2_font_size': 14,
            'body_font_size': 11,
            'line_spacing': 1.2
        }
    
    @staticmethod
    def create_custom_style(name: str, font_size: int = 11, font_color=black, 
                           space_before: int = 0, space_after: int = 6,
                           leading: int = None) -> ParagraphStyle:
        """Create a custom paragraph style with specified parameters."""
        if leading is None:
            leading = int(font_size * 1.2)
            
        return ParagraphStyle(
            name=name,
            fontSize=font_size,
            textColor=font_color,
            spaceBefore=space_before,
            spaceAfter=space_after,
            leading=leading
        )
    
    @staticmethod
    def format_citation_style(citation_text: str) -> str:
        """Format citation text for PDF display."""
        # Add proper citation formatting
        if not citation_text.strip():
            return ""
        
        # Ensure citation starts with proper formatting
        formatted = citation_text.strip()
        if not formatted.startswith('(') and not formatted.startswith('['):
            formatted = f"({formatted})"
        
        return f'<font size="9" color="gray">{formatted}</font>'
    
    @staticmethod
    def process_theological_formatting(text: str) -> str:
        """Apply theological document specific formatting."""
        # Scripture references - make them bold and blue
        text = re.sub(r'(\b(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|1 Samuel|2 Samuel|1 Kings|2 Kings|1 Chronicles|2 Chronicles|Ezra|Nehemiah|Esther|Job|Psalms|Proverbs|Ecclesiastes|Song of Songs|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|1 Corinthians|2 Corinthians|Galatians|Ephesians|Philippians|Colossians|1 Thessalonians|2 Thessalonians|1 Timothy|2 Timothy|Titus|Philemon|Hebrews|James|1 Peter|2 Peter|1 John|2 John|3 John|Jude|Revelation)\s+\d+:\d+(?:-\d+)?)', 
                     r'<b><font color="blue">\1</font></b>', text)
        
        # Greek/Hebrew terms - italicize
        text = re.sub(r'\b([αβγδεζηθικλμνξοπρστυφχψω]+)\b', r'<i>\1</i>', text)
        
        return text