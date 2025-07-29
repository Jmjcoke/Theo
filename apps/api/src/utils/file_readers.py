"""
File reading utilities for document processing.
Supports PDF, DOCX, TXT, MD, and JSON (Bible) file formats.
"""
import os
from typing import Optional, Dict, Any
import aiofiles
import PyPDF2
from docx import Document as DocxDocument
import chardet
import json


class FileReaderUtils:
    """Utility class for reading various document file formats."""
    
    async def read_file_content(self, file_path: str, mime_type: str) -> Optional[str]:
        """Read file content based on file type."""
        if not os.path.exists(file_path):
            return None
        
        try:
            if mime_type == 'application/pdf':
                return await self._read_pdf(file_path)
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return await self._read_docx(file_path)
            elif mime_type in ['application/json'] or file_path.endswith('.json'):
                return await self._read_json_bible(file_path)
            elif mime_type.startswith('text/') or file_path.endswith(('.txt', '.md')):
                return await self._read_text_file(file_path)
            else:
                return None
        except Exception:
            return None
    
    async def _read_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        import asyncio
        
        def _sync_pdf_read():
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        
        return await asyncio.get_event_loop().run_in_executor(None, _sync_pdf_read)
    
    async def _read_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        import asyncio
        
        def _sync_docx_read():
            doc = DocxDocument(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n".join(text)
        
        return await asyncio.get_event_loop().run_in_executor(None, _sync_docx_read)
    
    async def _read_text_file(self, file_path: str) -> str:
        """Read text file with encoding detection."""
        async with aiofiles.open(file_path, 'rb') as f:
            raw_data = await f.read()
        
        encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        
        async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
            return await f.read()
    
    async def _read_json_bible(self, file_path: str) -> str:
        """Extract text from Bible JSON file and format for processing."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                bible_data = json.loads(content)
            
            # Handle different JSON Bible formats
            if isinstance(bible_data, dict):
                # Format 1: Direct book-chapter-verse structure (like Psalms.json)
                if 'book' in bible_data and 'chapters' in bible_data:
                    return self._format_structured_bible_json(bible_data)
                # Format 2: Books array or verses array
                elif 'books' in bible_data or 'verses' in bible_data:
                    return self._format_structured_bible_json(bible_data)
                # Format 3: {book_name: {chapter: {verse: text}}}
                elif any(isinstance(v, dict) for v in bible_data.values()):
                    return self._format_nested_bible_json(bible_data)
                # Format 4: Simple verse list
                else:
                    return self._format_simple_bible_json(bible_data)
            
            # Format 4: Array of verses
            elif isinstance(bible_data, list):
                return self._format_verse_array_json(bible_data)
            
            else:
                raise ValueError("Unsupported Bible JSON format")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error reading Bible JSON: {str(e)}")
    
    def _format_nested_bible_json(self, bible_data: Dict[str, Any]) -> str:
        """Format nested Bible JSON: {book: {chapter: {verse: text}}}"""
        formatted_text = []
        
        for book_name, book_data in bible_data.items():
            if not isinstance(book_data, dict):
                continue
                
            formatted_text.append(f"\n{book_name}\n")
            
            for chapter_num, chapter_data in book_data.items():
                if not isinstance(chapter_data, dict):
                    continue
                    
                formatted_text.append(f"\n{book_name} {chapter_num}\n")
                
                for verse_num, verse_text in chapter_data.items():
                    formatted_text.append(f"{verse_num} {verse_text}")
        
        return "\n".join(formatted_text)
    
    def _format_structured_bible_json(self, bible_data: Dict[str, Any]) -> str:
        """Format structured Bible JSON with books/verses arrays"""
        formatted_text = []
        
        # Handle format with 'book' and 'chapters' at root level (like Psalms.json)
        if 'book' in bible_data and 'chapters' in bible_data:
            book_name = bible_data.get('book', 'Unknown Book')
            chapters = bible_data.get('chapters', [])
            
            formatted_text.append(f"\n{book_name}\n")
            
            for chapter in chapters:
                chapter_num = chapter.get('chapter', '1')
                formatted_text.append(f"\n{book_name} {chapter_num}\n")
                
                verses = chapter.get('verses', [])
                for verse in verses:
                    verse_num = verse.get('verse', '1')
                    verse_text = verse.get('text', '')
                    formatted_text.append(f"{verse_num} {verse_text}")
        
        # Handle format with nested 'books' array
        elif 'books' in bible_data:
            books = bible_data['books']
            for book in books:
                book_name = book.get('name', 'Unknown Book')
                formatted_text.append(f"\n{book_name}\n")
                
                chapters = book.get('chapters', [])
                for chapter_idx, chapter in enumerate(chapters, 1):
                    formatted_text.append(f"\n{book_name} {chapter_idx}\n")
                    
                    verses = chapter.get('verses', [])
                    for verse_idx, verse_text in enumerate(verses, 1):
                        formatted_text.append(f"{verse_idx} {verse_text}")
        
        # Handle format with direct 'verses' array
        elif 'verses' in bible_data:
            verses = bible_data['verses']
            current_book = ""
            current_chapter = 0
            
            for verse in verses:
                book = verse.get('book', 'Unknown Book')
                chapter = verse.get('chapter', 1)
                verse_num = verse.get('verse', 1)
                text = verse.get('text', '')
                
                if book != current_book:
                    current_book = book
                    formatted_text.append(f"\n{book}\n")
                
                if chapter != current_chapter:
                    current_chapter = chapter
                    formatted_text.append(f"\n{book} {chapter}\n")
                
                formatted_text.append(f"{verse_num} {text}")
        
        return "\n".join(formatted_text)
    
    def _format_simple_bible_json(self, bible_data: Dict[str, Any]) -> str:
        """Format simple Bible JSON format"""
        formatted_text = []
        
        for key, value in bible_data.items():
            if isinstance(value, str):
                formatted_text.append(f"{key} {value}")
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    formatted_text.append(f"{key} {sub_key} {sub_value}")
        
        return "\n".join(formatted_text)
    
    def _format_verse_array_json(self, bible_data: list) -> str:
        """Format Bible JSON as array of verse objects"""
        formatted_text = []
        current_book = ""
        current_chapter = 0
        
        for verse in bible_data:
            if not isinstance(verse, dict):
                continue
                
            book = verse.get('book', verse.get('book_name', 'Unknown Book'))
            chapter = verse.get('chapter', verse.get('chapter_number', 1))
            verse_num = verse.get('verse', verse.get('verse_number', 1))
            text = verse.get('text', verse.get('verse_text', ''))
            
            if book != current_book:
                current_book = book
                formatted_text.append(f"\n{book}\n")
            
            if chapter != current_chapter:
                current_chapter = chapter
                formatted_text.append(f"\n{book} {chapter}\n")
            
            formatted_text.append(f"{verse_num} {text}")
        
        return "\n".join(formatted_text)