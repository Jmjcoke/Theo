"""
Citation and excerpt utilities for chat nodes.
Extracted to maintain PocketFlow 150-line Node limit.
"""

from typing import Dict, Any


def create_excerpt(content: str, max_length: int = 200) -> str:
    """Create a readable excerpt from content"""
    if not content or len(content) <= max_length:
        return content
    truncated = content[:max_length]
    last_space = truncated.rfind(' ')
    return (truncated[:last_space] + "..." if last_space > max_length * 0.8 else truncated + "...")


def generate_citation(result: Dict[str, Any]) -> str:
    """Generate appropriate citation based on content type"""
    # Biblical citation
    if result.get('biblical_book') and result.get('biblical_chapter') and result.get('biblical_verse_start'):
        citation = f"{result['biblical_book']} {result['biblical_chapter']}:{result['biblical_verse_start']}"
        if result.get('biblical_verse_end') and result['biblical_verse_end'] != result['biblical_verse_start']:
            citation += f"-{result['biblical_verse_end']}"
        if result.get('biblical_version'):
            citation += f" ({result['biblical_version']})"
        return citation
    
    # Theological document citation
    if result.get('theological_document_name'):
        citation = result['theological_document_name']
        if result.get('theological_page_number'):
            citation += f", p. {result['theological_page_number']}"
        if result.get('theological_section'):
            citation += f", {result['theological_section']}"
        return citation
    
    return f"Document {result.get('document_id', 'Unknown')}"


def calculate_confidence(search_results: list, generated_answer: str) -> float:
    """Calculate confidence score based on context quality and answer characteristics"""
    if not search_results:
        return 0.3  # Low confidence without sources
    
    # Base confidence from search result relevance
    relevance_scores = [result.get('relevance', 0.0) for result in search_results[:5]]
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    
    # Adjust based on number of sources and answer length
    source_count_factor = min(len(search_results) / 3.0, 1.0)
    answer_length_factor = min(len(generated_answer) / 200.0, 1.0)
    
    # Combine factors
    confidence = (avg_relevance * 0.6) + (source_count_factor * 0.3) + (answer_length_factor * 0.1)
    return max(0.0, min(1.0, confidence))