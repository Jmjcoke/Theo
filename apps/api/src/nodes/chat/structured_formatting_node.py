"""
StructuredFormattingNode for template-based document formatting.

This node handles structured document formatting using predefined templates
for sermons, articles, and research papers with LLM-powered content structuring.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List
from pocketflow import AsyncNode
from src.utils.openai_client import get_openai_client

logger = logging.getLogger(__name__)

# Template definitions matching frontend types
TEMPLATES = {
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


class StructuredFormattingNode(AsyncNode):
    """Handles structured document formatting using predefined templates."""
    
    def __init__(self, model="gpt-4o", temperature=0.3):
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.client = get_openai_client()
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate formatting request and prepare template."""
        try:
            # Validate required fields
            required_fields = ['content', 'templateId', 'formattingOptions']
            for field in required_fields:
                if field not in shared_store:
                    return {"error": f"Missing required field: {field}"}
            
            # Validate template exists
            template_id = shared_store['templateId']
            if template_id not in TEMPLATES:
                return {"error": f"Unknown template: {template_id}"}
            
            # Validate content
            content = shared_store['content']
            if not content or len(content.strip()) == 0:
                return {"error": "Content cannot be empty"}
            
            if len(content) > 50000:  # 50KB limit
                return {"error": "Content too long (max 50KB)"}
            
            # Store template info
            shared_store['template'] = TEMPLATES[template_id]
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"StructuredFormattingNode prep error: {str(e)}")
            return {"error": f"Preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute structured formatting using the template."""
        start_time = time.time()
        
        try:
            content = shared_store['content']
            template = shared_store['template']
            formatting_options = shared_store['formattingOptions']
            context = shared_store.get('context', '')
            
            # Build the formatting prompt
            prompt = self._build_formatting_prompt(template, content, formatting_options, context)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert document formatter specializing in theological and academic writing. Format content according to the specified template while maintaining the original meaning and adding appropriate structure."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=4000
            )
            
            formatted_content = response.choices[0].message.content
            processing_time = int((time.time() - start_time) * 1000)
            
            # Determine applied formatting
            applied_formatting = self._get_applied_formatting(template, formatting_options)
            
            # Generate suggestions if needed
            suggestions = self._generate_suggestions(content, template, formatted_content)
            
            return {
                "success": True,
                "formattedContent": formatted_content,
                "appliedFormatting": applied_formatting,
                "templateUsed": template["name"],
                "processingTime": processing_time,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"StructuredFormattingNode exec error: {str(e)}")
            processing_time = int((time.time() - start_time) * 1000)
            return {
                "error": f"Formatting failed: {str(e)}",
                "processingTime": processing_time
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Post-processing for formatted content."""
        try:
            if shared_store.get("success"):
                logger.info(f"Successfully formatted content using {shared_store.get('templateUsed')} template")
            return {"success": True}
        except Exception as e:
            logger.error(f"StructuredFormattingNode post error: {str(e)}")
            return {"error": f"Post-processing failed: {str(e)}"}
    
    def _build_formatting_prompt(self, template: Dict[str, Any], content: str, formatting_options: Dict[str, Any], context: str) -> str:
        """Build the formatting prompt for the LLM."""
        
        # Base prompt
        prompt = f"""Format the following content according to the {template['name']} template structure.

Template Instructions: {template['instructions']}

Required Sections:"""
        
        # Add section structure
        for i, section in enumerate(template['sections'], 1):
            required_text = " (Required)" if section['required'] else " (Optional)"
            prompt += f"\n{i}. {section['title']}{required_text}"
        
        # Add formatting instructions
        prompt += f"\n\nFormatting Requirements:"
        prompt += f"\n- Header style: {formatting_options.get('headerStyle', 'normal')}"
        prompt += f"\n- Spacing: {formatting_options.get('spacing', 'normal')}"
        
        if formatting_options.get('useEmojis', False):
            prompt += "\n- Include appropriate emojis where they enhance readability"
            prompt += "\n- Use theological emojis like ✝️ 📖 ⭐ ✅ 💡 when relevant"
        
        bullet_style = formatting_options.get('bulletStyle', 'bullets')
        if bullet_style == 'bullets':
            prompt += "\n- Use bullet points (•) for lists"
        elif bullet_style == 'numbers':
            prompt += "\n- Use numbered lists (1., 2., 3.) for sequential items"
        elif bullet_style == 'checkmarks':
            prompt += "\n- Use checkmarks (✅) for actionable items and achievements"
        elif bullet_style == 'arrows':
            prompt += "\n- Use arrows (→) for process steps and progressions"
        
        if formatting_options.get('includeCallouts', False):
            prompt += "\n- Use callout boxes for important quotes, key insights, and applications"
            prompt += "\n- Format callouts with > blockquote syntax"
        
        prompt += "\n\nOutput Format:"
        prompt += "\n- Use proper Markdown formatting"
        prompt += "\n- Include clear section headers"
        prompt += "\n- Ensure good visual hierarchy"
        prompt += "\n- Make the document easy to read and professional"
        
        if context:
            prompt += f"\n\nAdditional Context: {context}"
        
        prompt += f"\n\nOriginal Content to Format:\n{content}"
        prompt += f"\n\nPlease structure this content according to the {template['name']} template format specified above."
        
        return prompt
    
    def _get_applied_formatting(self, template: Dict[str, Any], formatting_options: Dict[str, Any]) -> List[str]:
        """Determine what formatting was applied."""
        applied = [f"template:{template['name'].lower().replace(' ', '-')}"]
        
        if formatting_options.get('useEmojis'):
            applied.append("emojis")
        
        applied.append(f"bullets:{formatting_options.get('bulletStyle', 'bullets')}")
        applied.append(f"headers:{formatting_options.get('headerStyle', 'normal')}")
        applied.append(f"spacing:{formatting_options.get('spacing', 'normal')}")
        
        if formatting_options.get('includeCallouts'):
            applied.append("callouts")
        
        return applied
    
    def _generate_suggestions(self, original_content: str, template: Dict[str, Any], formatted_content: str) -> List[str]:
        """Generate suggestions for content improvement."""
        suggestions = []
        
        # Analyze content length
        original_words = len(original_content.split())
        formatted_words = len(formatted_content.split())
        
        # Template-specific suggestions
        if template['category'] == 'sermon':
            if original_words < 1500:
                suggestions.append("Consider expanding content - sermons typically range from 1500-3000 words")
            if '?' not in original_content:
                suggestions.append("Consider adding engaging questions for better audience connection")
            if 'scripture' not in original_content.lower() and 'bible' not in original_content.lower():
                suggestions.append("Consider adding more biblical references and scripture citations")
        
        elif template['category'] == 'article':
            if original_words < 800:
                suggestions.append("Consider expanding content - articles typically range from 800-2000 words")
            if len(original_content.split('\n\n')) < 3:
                suggestions.append("Consider breaking content into more paragraphs for better readability")
        
        elif template['category'] == 'research-paper':
            if original_words < 3000:
                suggestions.append("Consider expanding content - research papers typically range from 3000-8000 words")
            if 'citation' not in original_content.lower() and 'source' not in original_content.lower():
                suggestions.append("Consider adding more citations and scholarly sources")
        
        # Check for section completeness
        required_sections = [s for s in template['sections'] if s['required']]
        for section in required_sections:
            section_keywords = section['title'].lower().split()
            has_section = any(keyword in formatted_content.lower() for keyword in section_keywords)
            if not has_section:
                suggestions.append(f"Consider adding content for required section: {section['title']}")
        
        return suggestions[:5]  # Limit to 5 suggestions