"""
Document Templates Utility

Centralized template definitions for structured document formatting.
Extracted from structured_formatting_node.py to comply with PocketFlow 150-line limit.
"""

from typing import Dict, Any, List, Optional

# Template definitions matching frontend types
DOCUMENT_TEMPLATES = {
    "sermon-template": {
        "name": "Sermon",
        "category": "sermon",
        "sections": [
            {"id": "title", "title": "Sermon Title", "required": True},
            {"id": "text", "title": "Scripture Text", "required": True},
            {"id": "hook", "title": "Introduction/Hook", "required": True},
            {"id": "point1", "title": "Main Point 1", "required": True},
            {"id": "point2", "title": "Main Point 2", "required": True},
            {"id": "point3", "title": "Main Point 3", "required": True},
            {"id": "conclusion", "title": "Conclusion", "required": True}
        ],
        "instructions": """Generate a well-structured sermon following traditional homiletic principles. Each main point should include:
1. Clear theological explanation of the text
2. Relevant illustration or example
3. Practical application for daily life
Use theological terminology appropriately and maintain reverent tone throughout."""
    },
    "article-template": {
        "name": "Article",
        "category": "article",
        "sections": [
            {"id": "title", "title": "Article Title", "required": True},
            {"id": "subtitle", "title": "Subtitle/Tagline", "required": False},
            {"id": "introduction", "title": "Introduction", "required": True},
            {"id": "body", "title": "Main Content", "required": True},
            {"id": "practical-application", "title": "Practical Application", "required": True},
            {"id": "conclusion", "title": "Conclusion", "required": True}
        ],
        "instructions": """Create an engaging, well-researched article that combines theological depth with practical relevance. Use:
- Clear, accessible language
- Biblical support for key points
- Relevant contemporary examples
- Actionable insights readers can apply immediately
Maintain an encouraging, instructive tone throughout."""
    },
    "research-paper-template": {
        "name": "Research Paper",
        "category": "research-paper",
        "sections": [
            {"id": "title-page", "title": "Title Page", "required": True},
            {"id": "abstract", "title": "Abstract", "required": True},
            {"id": "introduction", "title": "Introduction", "required": True},
            {"id": "literature-review", "title": "Literature Review", "required": True},
            {"id": "methodology", "title": "Methodology", "required": True},
            {"id": "findings", "title": "Findings/Analysis", "required": True},
            {"id": "discussion", "title": "Discussion", "required": True},
            {"id": "conclusion", "title": "Conclusion", "required": True},
            {"id": "bibliography", "title": "Bibliography", "required": True}
        ],
        "instructions": """Generate a scholarly research paper following academic standards. Requirements:
- Use formal, academic tone throughout
- Provide proper citations and evidence for all claims
- Follow logical argument structure
- Demonstrate engagement with scholarly sources
- Maintain objective, analytical perspective
- Use appropriate theological and academic terminology"""
    }
}


class DocumentTemplateUtils:
    """Utility class for document template operations"""
    
    @staticmethod
    def get_template(template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID"""
        return DOCUMENT_TEMPLATES.get(template_id)
    
    @staticmethod
    def list_templates() -> List[str]:
        """Get list of available template IDs"""
        return list(DOCUMENT_TEMPLATES.keys())
    
    @staticmethod
    def validate_template_id(template_id: str) -> bool:
        """Check if template ID exists"""
        return template_id in DOCUMENT_TEMPLATES
    
    @staticmethod
    def get_template_sections(template_id: str) -> List[Dict[str, Any]]:
        """Get sections for a specific template"""
        template = DOCUMENT_TEMPLATES.get(template_id)
        return template.get("sections", []) if template else []
    
    @staticmethod
    def get_template_instructions(template_id: str) -> str:
        """Get formatting instructions for a template"""
        template = DOCUMENT_TEMPLATES.get(template_id)
        return template.get("instructions", "") if template else ""
    
    @staticmethod
    def get_required_sections(template_id: str) -> List[str]:
        """Get list of required section IDs for a template"""
        sections = DocumentTemplateUtils.get_template_sections(template_id)
        return [section["id"] for section in sections if section.get("required", False)]
    
    @staticmethod
    def get_template_category(template_id: str) -> str:
        """Get category for a template"""
        template = DOCUMENT_TEMPLATES.get(template_id)
        return template.get("category", "") if template else ""