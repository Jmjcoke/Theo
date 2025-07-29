"""
Chunking utilities for DocumentChunkerNode.
Extracted to maintain PocketFlow 150-line limit.
"""
import re
from typing import Dict, Any, List
from datetime import datetime, timezone


class ChunkingUtils:
    """Utility class for document chunking operations."""
    
    def chunk_biblical_document(self, content: str, document_id: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk biblical document into groups of 5 verses with 1-verse overlap."""
        verses = self._parse_biblical_verses(content)
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(verses), 4):  # Step by 4 for 1-verse overlap
            verse_group = verses[i:i + 5]  # Take up to 5 verses
            if not verse_group:
                break
                
            chunk_content = "\n".join([v['text'] for v in verse_group])
            
            # Determine verse range
            start_verse = verse_group[0]['verse']
            end_verse = verse_group[-1]['verse']
            book = verse_group[0]['book']
            chapter = verse_group[0]['chapter']
            
            citation = f"{book} {chapter}:{start_verse}"
            if end_verse != start_verse:
                citation += f"-{end_verse}"
            
            chunk = {
                "chunk_id": f"{document_id}_chunk_{chunk_id}",
                "chunk_index": chunk_id,
                "content": chunk_content,
                "chunk_type": "biblical_verse_group",
                "document_id": document_id,
                "metadata": {
                    "book": book,
                    "chapter": chapter,
                    "verse_start": start_verse,
                    "verse_end": end_verse,
                    "citation": citation,
                    "overlap_with_previous": chunk_id > 0,
                    "overlap_with_next": i + 4 < len(verses)
                }
            }
            
            chunks.append(chunk)
            chunk_id += 1
        
        return chunks
    
    def chunk_theological_document(self, content: str, document_id: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk theological document into 1000-character segments with 200-character overlap."""
        chunks = []
        chunk_id = 0
        chunk_size = 1000
        overlap_size = 200
        
        # Clean and normalize text
        cleaned_content = self._clean_text(content)
        paragraphs = self._split_into_paragraphs(cleaned_content)
        
        current_pos = 0
        total_length = len(cleaned_content)
        
        while current_pos < total_length:
            end_pos = min(current_pos + chunk_size, total_length)
            
            # Try to find a good boundary (sentence or word)
            if end_pos < total_length:
                end_pos = self._find_smart_boundary(cleaned_content, current_pos, end_pos)
            
            chunk_text = cleaned_content[current_pos:end_pos].strip()
            if not chunk_text:
                break
            
            # Find paragraph index
            paragraph_index = self._find_paragraph_index(paragraphs, current_pos)
            
            chunk = {
                "chunk_id": f"{document_id}_chunk_{chunk_id}",
                "chunk_index": chunk_id,
                "content": chunk_text,
                "chunk_type": "theological_segment",
                "document_id": document_id,
                "metadata": {
                    "char_start": current_pos,
                    "char_end": end_pos,
                    "paragraph_index": paragraph_index,
                    "overlap_with_previous": chunk_id > 0,
                    "overlap_with_next": end_pos < total_length
                }
            }
            
            chunks.append(chunk)
            chunk_id += 1
            
            # Move position forward with overlap
            current_pos = max(current_pos + chunk_size - overlap_size, end_pos)
        
        return chunks
    
    def _parse_biblical_verses(self, content: str) -> List[Dict[str, Any]]:
        """Parse biblical text to extract verse information."""
        verses = []
        lines = content.split('\n')
        
        current_book = "Unknown"
        current_chapter = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to detect book and chapter headers
            book_chapter_match = re.match(r'^([A-Za-z\s]+)\s+(\d+)', line)
            if book_chapter_match and len(line.split()) <= 3:
                current_book = book_chapter_match.group(1).strip()
                current_chapter = int(book_chapter_match.group(2))
                continue
            
            # Try to extract verse number and text
            verse_match = re.match(r'^(\d+)\s+(.+)', line)
            if verse_match:
                verse_num = int(verse_match.group(1))
                verse_text = verse_match.group(2).strip()
                
                verses.append({
                    'book': current_book,
                    'chapter': current_chapter,
                    'verse': verse_num,
                    'text': f"{verse_num} {verse_text}"
                })
        
        return verses
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for chunking."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        return text.strip()
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs for boundary detection."""
        return [p.strip() for p in text.split('\n\n') if p.strip()]
    
    def _find_smart_boundary(self, text: str, start: int, end: int) -> int:
        """Find a smart boundary to avoid breaking mid-word or mid-sentence."""
        if end >= len(text):
            return end
        
        # Look for sentence boundary within last 100 characters
        search_start = max(start, end - 100)
        sentence_pattern = r'[.!?]\s+'
        
        for match in re.finditer(sentence_pattern, text[search_start:end]):
            boundary = search_start + match.end()
            if boundary > start + 200:  # Ensure minimum chunk size
                return boundary
        
        # Look for word boundary
        for i in range(end - 1, max(start, end - 50), -1):
            if text[i].isspace():
                return i
        
        return end
    
    def _find_paragraph_index(self, paragraphs: List[str], position: int) -> int:
        """Find which paragraph contains the given character position."""
        current_pos = 0
        for i, paragraph in enumerate(paragraphs):
            if current_pos <= position < current_pos + len(paragraph):
                return i
            current_pos += len(paragraph) + 2  # Account for paragraph separator
        return len(paragraphs) - 1 if paragraphs else 0
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')