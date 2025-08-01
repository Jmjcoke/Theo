"""
FormatPostProcessorNode for generating suggestions and final formatting output.

Split from structured_formatting_node.py to comply with PocketFlow 150-line limit.
Handles the post phase of structured document formatting and suggestions generation.
"""

import logging
from typing import Dict, Any, List
from pocketflow import AsyncNode

logger = logging.getLogger(__name__)


class FormatPostProcessorNode(AsyncNode):
    """Generates suggestions and produces final formatted document output."""
    
    def __init__(self):
        super().__init__()
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Prepare for post-processing the formatted content."""
        try:
            # Check that formatting was successful
            if not shared_store.get('formatted_content'):
                return {"error": "No formatted content available for post-processing"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"FormatPostProcessorNode prep error: {str(e)}")
            return {"error": f"Post-processing preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute post-processing: generate suggestions and finalize output."""
        try:
            # Get formatting results
            formatted_content = shared_store['formatted_content']
            original_content = shared_store.get('original_content', '')
            template_used = shared_store.get('template_used', {})
            formatting_options = shared_store.get('formattingOptions', {})
            
            # Generate improvement suggestions
            suggestions = self._generate_suggestions(original_content, template_used, formatted_content)
            
            # Calculate content metrics
            metrics = self._calculate_content_metrics(formatted_content, original_content)
            
            # Generate final response structure
            final_result = {
                'success': True,
                'formatted_content': formatted_content,
                'original_content': original_content,
                'template_name': template_used.get('name', 'Unknown'),
                'suggestions': suggestions,
                'metrics': metrics,
                'applied_formatting': shared_store.get('applied_formatting', []),
                'processing_metadata': {
                    'model_used': shared_store.get('model_used', 'unknown'),
                    'processing_time': shared_store.get('processing_time', 0),
                    'token_usage': shared_store.get('token_usage', 0)
                }
            }
            
            return final_result
            
        except Exception as e:
            error_msg = f"Post-processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'formatted_content': shared_store.get('formatted_content', ''),
                'suggestions': [],
                'metrics': {}
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store final results in shared store."""
        try:
            # Final results are stored by the framework
            logger.info("Format post-processing completed")
            return {"next_state": "completed"}
            
        except Exception as e:
            logger.error(f"FormatPostProcessorNode post error: {str(e)}")
            return {"next_state": "failed"}
    
    def _generate_suggestions(self, original_content: str, template: Dict[str, Any], 
                            formatted_content: str) -> List[str]:
        """Generate improvement suggestions based on the formatting results."""
        category = template.get('category', '')
        suggestions = []
        
        # Basic suggestions by category
        if category == 'sermon':
            suggestions = ["Add practical examples", "Include Scripture references", "Strengthen conclusion"]
        elif category == 'article':
            suggestions = ["Add contemporary examples", "Include discussion questions", "Enhance practical application"]
        elif category == 'research-paper':
            suggestions = ["Verify citations", "Review methodology", "Check bibliography"]
        else:
            suggestions = ["Review content structure", "Check formatting consistency", "Enhance readability"]
        
        return suggestions[:3]
    
    def _calculate_content_metrics(self, formatted_content: str, original_content: str) -> Dict[str, Any]:
        """Calculate useful metrics about the formatted content."""
        try:
            formatted_words = len(formatted_content.split())
            original_words = len(original_content.split()) if original_content else 0
            
            formatted_chars = len(formatted_content)
            original_chars = len(original_content) if original_content else 0
            
            # Calculate reading time (average 200 words per minute)
            reading_time_minutes = max(1, formatted_words // 200)
            
            # Calculate expansion ratio
            expansion_ratio = formatted_words / original_words if original_words > 0 else 1.0
            
            metrics = {
                'word_count': formatted_words,
                'character_count': formatted_chars,
                'estimated_reading_time_minutes': reading_time_minutes,
                'paragraph_count': len([p for p in formatted_content.split('\n\n') if p.strip()]),
                'expansion_ratio': round(expansion_ratio, 2),
                'original_word_count': original_words,
                'content_density': round(formatted_words / max(1, formatted_chars) * 100, 2)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating content metrics: {str(e)}")
            return {
                'word_count': 0,
                'character_count': 0,
                'estimated_reading_time_minutes': 0,
                'paragraph_count': 0,
                'expansion_ratio': 1.0,
                'original_word_count': 0,
                'content_density': 0.0
            }