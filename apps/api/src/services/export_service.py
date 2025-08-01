"""
Export Service
Handles document export functionality (PDF, DOCX, Markdown)
"""

import os
import sqlite3
import json
import asyncio
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from ..models.editor_models import *


class ExportService:
    def __init__(self):
        self.db_path = "theo.db"
        self.export_dir = "exports"
        self.ensure_export_directory()

    def ensure_export_directory(self):
        """Ensure export directory exists"""
        Path(self.export_dir).mkdir(exist_ok=True)

    async def start_export(self, doc_id: int, export_request: ExportRequest, user_id: int) -> int:
        """Start document export process"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Create export record
            cursor.execute("""
                INSERT INTO editor_exports 
                (document_id, user_id, export_format, export_status, file_path, file_size)
                VALUES (?, ?, ?, 'pending', '', 0)
            """, (doc_id, user_id, export_request.format))
            
            export_id = cursor.lastrowid
            conn.commit()
            return export_id
            
        finally:
            conn.close()

    async def process_export(self, export_id: int, document: EditorDocumentResponse, export_request: ExportRequest):
        """Process the actual export (runs in background)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Update status to processing
            cursor.execute("""
                UPDATE editor_exports 
                SET export_status = 'processing' 
                WHERE id = ?
            """, (export_id,))
            conn.commit()

            # Generate filename
            safe_title = "".join(c for c in document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length and replace spaces
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{timestamp}.{export_request.format}"
            file_path = os.path.join(self.export_dir, filename)

            # Process based on format
            if export_request.format == ExportFormat.MARKDOWN:
                await self._export_markdown(document, file_path, export_request)
            elif export_request.format == ExportFormat.PDF:
                await self._export_pdf(document, file_path, export_request)
            elif export_request.format == ExportFormat.DOCX:
                await self._export_docx(document, file_path, export_request)

            # Get file size
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            # Update export record
            cursor.execute("""
                UPDATE editor_exports 
                SET export_status = 'completed', file_path = ?, file_size = ?
                WHERE id = ?
            """, (file_path, file_size, export_id))
            conn.commit()

        except Exception as e:
            # Update status to failed
            cursor.execute("""
                UPDATE editor_exports 
                SET export_status = 'failed', error_message = ?
                WHERE id = ?
            """, (str(e), export_id))
            conn.commit()
            
        finally:
            conn.close()

    async def _export_markdown(self, document: EditorDocumentResponse, file_path: str, export_request: ExportRequest):
        """Export document as Markdown"""
        content = f"# {document.title}\n\n"
        content += f"*Document Type: {document.document_type.replace('_', ' ').title()}*\n\n"
        content += f"*Created: {document.created_at}*\n\n"
        content += f"*Word Count: {document.word_count} words*\n\n"
        content += "---\n\n"
        content += document.content
        
        # Add citations if requested
        if export_request.include_citations:
            citations = await self._get_document_citations(document.id)
            if citations:
                content += "\n\n## Sources and Citations\n\n"
                for i, citation in enumerate(citations, 1):
                    content += f"{i}. {citation.citation_text}\n"
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    async def _export_pdf(self, document: EditorDocumentResponse, file_path: str, export_request: ExportRequest):
        """Export document as PDF using Pandoc"""
        # First create markdown content
        temp_md = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        
        try:
            # Create markdown content with proper formatting
            content = f"---\ntitle: \"{document.title}\"\nauthor: \"Theo User\"\ndate: \"{document.created_at}\"\n---\n\n"
            content += document.content
            
            # Add citations
            if export_request.include_citations:
                citations = await self._get_document_citations(document.id)
                if citations:
                    content += "\n\n# References\n\n"
                    for i, citation in enumerate(citations, 1):
                        content += f"{i}. {citation.citation_text}\n"
            
            temp_md.write(content)
            temp_md.close()

            # Use pandoc to convert to PDF
            pandoc_cmd = [
                'pandoc',
                temp_md.name,
                '-o', file_path,
                '--pdf-engine=xelatex',
                '--variable', 'mainfont=Times New Roman',
                '--variable', 'fontsize=12pt',
                '--variable', 'linestretch=1.5',
                '--variable', 'margin-left=1in',
                '--variable', 'margin-right=1in',
                '--variable', 'margin-top=1in',
                '--variable', 'margin-bottom=1in'
            ]
            
            # Apply custom styling if provided
            if export_request.custom_styling:
                styling = export_request.custom_styling
                if styling.get('font_size'):
                    pandoc_cmd.extend(['--variable', f'fontsize={styling["font_size"]}'])
                if styling.get('font_family'):
                    pandoc_cmd.extend(['--variable', f'mainfont={styling["font_family"]}'])

            # Execute pandoc
            result = subprocess.run(pandoc_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"Pandoc failed: {result.stderr}")
                
        finally:
            # Clean up temp file
            os.unlink(temp_md.name)

    async def _export_docx(self, document: EditorDocumentResponse, file_path: str, export_request: ExportRequest):
        """Export document as DOCX using Pandoc"""
        # Create temporary markdown file
        temp_md = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        
        try:
            # Create markdown content
            content = f"# {document.title}\n\n"
            content += document.content
            
            # Add citations
            if export_request.include_citations:
                citations = await self._get_document_citations(document.id)
                if citations:
                    content += "\n\n## References\n\n"
                    for i, citation in enumerate(citations, 1):
                        content += f"{i}. {citation.citation_text}\n"
            
            temp_md.write(content)
            temp_md.close()

            # Use pandoc to convert to DOCX
            pandoc_cmd = [
                'pandoc',
                temp_md.name,
                '-o', file_path,
                '--reference-doc=templates/reference.docx' if os.path.exists('templates/reference.docx') else '',
                '--filter=pandoc-citeproc' if export_request.include_citations else ''
            ]
            
            # Remove empty arguments
            pandoc_cmd = [arg for arg in pandoc_cmd if arg]

            # Execute pandoc
            result = subprocess.run(pandoc_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"Pandoc failed: {result.stderr}")
                
        finally:
            # Clean up temp file
            os.unlink(temp_md.name)

    async def get_export_status(self, export_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get export status"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM editor_exports 
                WHERE id = ? AND user_id = ?
            """, (export_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return dict(row)
            
        finally:
            conn.close()

    async def get_export_file(self, export_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get export file information for download"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM editor_exports 
                WHERE id = ? AND user_id = ? AND export_status = 'completed'
            """, (export_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Determine media type
            format_to_media_type = {
                'pdf': 'application/pdf',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'markdown': 'text/markdown'
            }
            
            filename = os.path.basename(row['file_path'])
            
            return {
                'file_path': row['file_path'],
                'filename': filename,
                'media_type': format_to_media_type.get(row['export_format'], 'application/octet-stream'),
                'file_size': row['file_size']
            }
            
        finally:
            conn.close()

    async def _get_document_citations(self, doc_id: int) -> List[CitationResponse]:
        """Get citations for a document"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM editor_citations 
                WHERE document_id = ? 
                ORDER BY created_at ASC
            """, (doc_id,))
            
            rows = cursor.fetchall()
            return [CitationResponse(**dict(row)) for row in rows]
            
        finally:
            conn.close()

    async def cleanup_old_exports(self, days_old: int = 7):
        """Clean up old export files"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get old export records
            cursor.execute("""
                SELECT file_path FROM editor_exports 
                WHERE created_at < date('now', '-{} days') 
                AND export_status = 'completed'
            """.format(days_old))
            
            old_files = cursor.fetchall()
            
            # Delete files and records
            for (file_path,) in old_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete database records
            cursor.execute("""
                DELETE FROM editor_exports 
                WHERE created_at < date('now', '-{} days')
            """.format(days_old))
            
            conn.commit()
            
        finally:
            conn.close()

    async def check_health(self) -> bool:
        """Check export service health"""
        try:
            # Check if pandoc is available
            result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True, timeout=5)
            pandoc_available = result.returncode == 0
            
            # Check export directory
            export_dir_exists = os.path.exists(self.export_dir) and os.path.isdir(self.export_dir)
            
            # Check database connectivity
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM editor_exports")
            conn.close()
            
            return pandoc_available and export_dir_exists
            
        except Exception:
            return False

    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats"""
        return ['pdf', 'docx', 'markdown']

    async def get_export_stats(self, user_id: int) -> Dict[str, Any]:
        """Get export statistics for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Total exports
            cursor.execute("SELECT COUNT(*) FROM editor_exports WHERE user_id = ?", (user_id,))
            total_exports = cursor.fetchone()[0]
            
            # Exports by format
            cursor.execute("""
                SELECT export_format, COUNT(*) as count 
                FROM editor_exports 
                WHERE user_id = ? 
                GROUP BY export_format
            """, (user_id,))
            
            exports_by_format = {row['export_format']: row['count'] for row in cursor.fetchall()}
            
            # Recent exports
            cursor.execute("""
                SELECT export_format, export_status, created_at 
                FROM editor_exports 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (user_id,))
            
            recent_exports = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_exports': total_exports,
                'exports_by_format': exports_by_format,
                'recent_exports': recent_exports
            }
            
        finally:
            conn.close()