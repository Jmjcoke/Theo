"""
Citation and excerpt utilities for chat nodes.
Extracted to maintain PocketFlow 150-line Node limit.
"""

import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional


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


def enrich_search_results_with_metadata(search_results: List[Dict[str, Any]], sqlite_db_path: str = "theo.db") -> List[Dict[str, Any]]:
    """
    Enrich search results with document metadata from SQLite database.
    
    Args:
        search_results: List of search results from Supabase
        sqlite_db_path: Path to SQLite database
        
    Returns:
        Enhanced search results with document metadata
    """
    logger = logging.getLogger(__name__)
    
    if not search_results:
        return search_results
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()
        
        # Get unique document IDs from search results
        document_ids = set()
        for result in search_results:
            doc_id = result.get('metadata', {}).get('document_id')
            if doc_id:
                document_ids.add(doc_id)
        
        if not document_ids:
            logger.warning("No document IDs found in search results")
            return search_results
        
        # Query document metadata from SQLite
        placeholders = ','.join('?' * len(document_ids))
        query = f"""
        SELECT id, filename, original_filename, document_type, file_path, metadata
        FROM documents 
        WHERE id IN ({placeholders})
        """
        
        cursor.execute(query, list(document_ids))
        db_documents = cursor.fetchall()
        
        # Create a lookup dictionary
        doc_metadata_lookup = {}
        for doc in db_documents:
            doc_id, filename, original_filename, doc_type, file_path, metadata_json = doc
            
            # Parse metadata JSON
            metadata = {}
            if metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for document {doc_id}")
            
            doc_metadata_lookup[str(doc_id)] = {
                'filename': filename,
                'original_filename': original_filename or metadata.get('original_filename'),
                'document_type': doc_type,
                'file_path': file_path,
                'metadata': metadata
            }
        
        # Enrich search results
        enriched_results = []
        for result in search_results:
            enriched_result = result.copy()
            
            doc_id = result.get('metadata', {}).get('document_id')
            if doc_id and str(doc_id) in doc_metadata_lookup:
                doc_info = doc_metadata_lookup[str(doc_id)]
                
                # Add enhanced metadata
                enriched_result['document_title'] = doc_info['original_filename'] or doc_info['filename']
                enriched_result['document_type'] = doc_info['document_type']
                enriched_result['file_path'] = doc_info['file_path']
                
                # Add chunk information for page/paragraph context
                chunk_index = result.get('metadata', {}).get('chunk_index', 0)
                enriched_result['chunk_index'] = chunk_index
                enriched_result['approximate_page'] = (chunk_index // 3) + 1  # Rough estimate: 3 chunks per page
                enriched_result['paragraph_indicator'] = f"Section {chunk_index + 1}"
                
                # Create a better title
                title = doc_info['original_filename'] or doc_info['filename']
                if title:
                    # Clean up the title - remove UUID prefixes and file extensions
                    if '_' in title and len(title.split('_')[0]) > 30:  # Likely has UUID prefix
                        title = '_'.join(title.split('_')[1:])
                    if title.endswith('.pdf'):
                        title = title[:-4]
                    enriched_result['title'] = title
                else:
                    enriched_result['title'] = f"Document {doc_id}"
                
                # Enhanced citation
                citation = title
                if enriched_result['approximate_page'] > 1:
                    citation += f", p. {enriched_result['approximate_page']}"
                citation += f", {enriched_result['paragraph_indicator']}"
                enriched_result['citation'] = citation
            
            enriched_results.append(enriched_result)
        
        conn.close()
        logger.info(f"Enriched {len(enriched_results)} search results with document metadata")
        return enriched_results
        
    except Exception as e:
        logger.error(f"Failed to enrich search results with metadata: {str(e)}")
        return search_results


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