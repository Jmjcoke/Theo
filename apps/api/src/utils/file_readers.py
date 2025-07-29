"""
File reading utilities for document processing.
Supports PDF, DOCX, TXT, and MD file formats.
"""
import os
from typing import Optional
import aiofiles
import PyPDF2
from docx import Document as DocxDocument
import chardet


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