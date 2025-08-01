"""
Editor Service
Handles document editing business logic and database operations
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..models.editor_models import *
from ..utils.openai_client import get_openai_client


class EditorService:
    def __init__(self):
        self.db_path = "theo.db"

    async def create_document(self, doc: CreateEditorDocument, user_id: int) -> EditorDocumentResponse:
        """Create a new document"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Calculate initial stats
            word_count = self._calculate_word_count(doc.content or "")
            reading_time = self._calculate_reading_time(word_count)
            
            # Insert document
            cursor.execute("""
                INSERT INTO editor_documents 
                (user_id, title, content, template_id, document_type, word_count, reading_time, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, doc.title, doc.content or "", doc.template_id, 
                doc.document_type, word_count, reading_time, 
                json.dumps(doc.metadata) if doc.metadata else None
            ))
            
            document_id = cursor.lastrowid
            conn.commit()
            
            # Create initial version
            await self._create_document_version(document_id, doc.content or "", "Initial version")
            
            # Fetch and return the created document
            return await self.get_document(document_id, user_id)
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    async def get_document(self, doc_id: int, user_id: int) -> Optional[EditorDocumentResponse]:
        """Get a document by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM editor_documents 
                WHERE id = ? AND user_id = ?
            """, (doc_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return self._row_to_document_response(row)
            
        finally:
            conn.close()

    async def list_documents(
        self, 
        user_id: int, 
        document_type: Optional[DocumentType] = None,
        status_filter: Optional[DocumentStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[EditorDocumentSummary]:
        """List user's documents with filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM editor_documents WHERE user_id = ?"
            params = [user_id]
            
            if document_type:
                query += " AND document_type = ?"
                params.append(document_type)
                
            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)
                
            query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_document_summary(row) for row in rows]
            
        finally:
            conn.close()

    async def update_document(self, doc_id: int, doc: UpdateEditorDocument, user_id: int) -> Optional[EditorDocumentResponse]:
        """Update an existing document"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # First verify ownership
            cursor.execute("SELECT * FROM editor_documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
            existing = cursor.fetchone()
            if not existing:
                return None

            # Build update query dynamically
            updates = []
            params = []
            
            if doc.title is not None:
                updates.append("title = ?")
                params.append(doc.title)
                
            if doc.content is not None:
                updates.append("content = ?")
                params.append(doc.content)
                # Update stats when content changes
                word_count = self._calculate_word_count(doc.content)
                reading_time = self._calculate_reading_time(word_count)
                updates.extend(["word_count = ?", "reading_time = ?"])
                params.extend([word_count, reading_time])
                
            if doc.template_id is not None:
                updates.append("template_id = ?")
                params.append(doc.template_id)
                
            if doc.document_type is not None:
                updates.append("document_type = ?")
                params.append(doc.document_type)
                
            if doc.status is not None:
                updates.append("status = ?")
                params.append(doc.status)
                
            if doc.metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(doc.metadata))
            
            if not updates:
                return await self.get_document(doc_id, user_id)
            
            # Add timestamp and ID
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(doc_id)
            
            query = f"UPDATE editor_documents SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            # Create version if content changed
            if doc.content is not None:
                await self._create_document_version(doc_id, doc.content, "Content updated")
            
            conn.commit()
            return await self.get_document(doc_id, user_id)
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    async def delete_document(self, doc_id: int, user_id: int) -> bool:
        """Delete a document"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM editor_documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
            
        finally:
            conn.close()

    async def format_document_content(self, doc_id: int, format_request: FormatRequest, user_id: int) -> Dict[str, Any]:
        """Apply natural language formatting using OpenAI"""
        # Verify document ownership
        document = await self.get_document(doc_id, user_id)
        if not document:
            raise ValueError("Document not found")

        try:
            # Create formatting prompt
            system_prompt = """You are a document formatting assistant. Apply the requested formatting changes to the provided text. 
            Respond with JSON containing:
            - "formatted_content": the updated text with formatting applied
            - "changes": array of changes made
            - "explanation": brief explanation of what was done
            
            Common commands:
            - "make this bold" -> **text**
            - "create bullet list" -> • item format
            - "add heading" -> # Heading format
            - "make outline" -> structured format with numbers/bullets
            """

            user_prompt = f"""
            Command: {format_request.command}
            
            Original content:
            {document.content}
            
            Selected text: {format_request.selected_text or "None"}
            """

            openai_client = get_openai_client()
            response = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content)
            
            # Update document with formatted content
            if result.get("formatted_content"):
                await self.update_document(doc_id, UpdateEditorDocument(
                    content=result["formatted_content"]
                ), user_id)
            
            return result

        except Exception as e:
            return {
                "error": str(e),
                "formatted_content": document.content,
                "changes": [],
                "explanation": "Formatting failed"
            }

    async def transfer_content(self, doc_id: int, transfer: ContentTransfer, user_id: int) -> Dict[str, Any]:
        """Transfer content from chat to document"""
        document = await self.get_document(doc_id, user_id)
        if not document:
            raise ValueError("Document not found")

        try:
            # Prepare content for insertion
            new_content = f"{document.content}\n\n{transfer.content}\n\n"
            
            # Update document
            await self.update_document(doc_id, UpdateEditorDocument(
                content=new_content,
                title=transfer.title if transfer.title and document.title == "Untitled Document" else document.title
            ), user_id)
            
            # Add citations if sources provided
            citations_added = 0
            if transfer.sources:
                for source in transfer.sources:
                    await self.add_citation(doc_id, CreateCitation(
                        source_id=source.get("id", "unknown"),
                        citation_text=source.get("title", "Unknown source")
                    ))
                    citations_added += 1
            
            return {
                "success": True,
                "citations_added": citations_added,
                "content_length": len(transfer.content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "citations_added": 0
            }

    async def add_citation(self, doc_id: int, citation: CreateCitation) -> CitationResponse:
        """Add a citation to a document"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO editor_citations 
                (document_id, source_id, citation_text, position_start, position_end, citation_format)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                doc_id, citation.source_id, citation.citation_text,
                citation.position_start, citation.position_end, citation.citation_format
            ))
            
            citation_id = cursor.lastrowid
            conn.commit()
            
            # Fetch the created citation
            cursor.execute("SELECT * FROM editor_citations WHERE id = ?", (citation_id,))
            row = cursor.fetchone()
            
            return CitationResponse(**dict(row))
            
        finally:
            conn.close()

    async def get_citations(self, doc_id: int) -> List[CitationResponse]:
        """Get all citations for a document"""
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

    async def delete_citation(self, citation_id: int, user_id: int) -> bool:
        """Delete a citation (with ownership verification)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Verify user owns the document containing this citation
            cursor.execute("""
                DELETE FROM editor_citations 
                WHERE id = ? AND document_id IN (
                    SELECT id FROM editor_documents WHERE user_id = ?
                )
            """, (citation_id, user_id))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
            
        finally:
            conn.close()

    async def get_document_versions(self, doc_id: int, limit: int = 10) -> List[DocumentVersionResponse]:
        """Get document version history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM editor_document_versions 
                WHERE document_id = ? 
                ORDER BY version_number DESC 
                LIMIT ?
            """, (doc_id, limit))
            
            rows = cursor.fetchall()
            return [DocumentVersionResponse(**dict(row)) for row in rows]
            
        finally:
            conn.close()

    async def restore_document_version(self, doc_id: int, version_id: int, user_id: int) -> bool:
        """Restore document to a previous version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get the version content
            cursor.execute("""
                SELECT content FROM editor_document_versions 
                WHERE id = ? AND document_id = ?
            """, (version_id, doc_id))
            
            version_row = cursor.fetchone()
            if not version_row:
                return False
            
            # Update the document
            await self.update_document(doc_id, UpdateEditorDocument(
                content=version_row[0]
            ), user_id)
            
            return True
            
        finally:
            conn.close()

    async def get_user_stats(self, user_id: int) -> UserDocumentStats:
        """Get user document statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM editor_documents WHERE user_id = ?", (user_id,))
            total_documents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM editor_documents WHERE user_id = ? AND status = 'draft'", (user_id,))
            draft_documents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM editor_documents WHERE user_id = ? AND status = 'published'", (user_id,))
            published_documents = cursor.fetchone()[0]
            
            # Word count stats
            cursor.execute("SELECT SUM(word_count), AVG(word_count) FROM editor_documents WHERE user_id = ?", (user_id,))
            word_stats = cursor.fetchone()
            total_words = word_stats[0] or 0
            avg_length = word_stats[1] or 0
            
            # Most used template
            cursor.execute("""
                SELECT template_id, COUNT(*) as usage_count 
                FROM editor_documents 
                WHERE user_id = ? AND template_id IS NOT NULL
                GROUP BY template_id 
                ORDER BY usage_count DESC 
                LIMIT 1
            """, (user_id,))
            template_row = cursor.fetchone()
            most_used_template = template_row[0] if template_row else None
            
            # Recent activity
            cursor.execute("""
                SELECT 'created' as type, id as document_id, title as document_title, created_at as timestamp
                FROM editor_documents 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 5
            """, (user_id,))
            recent_activity = [dict(row) for row in cursor.fetchall()]
            
            return UserDocumentStats(
                total_documents=total_documents,
                draft_documents=draft_documents,
                published_documents=published_documents,
                total_words_written=total_words,
                average_document_length=avg_length,
                most_used_template=most_used_template,
                recent_activity=recent_activity
            )
            
        finally:
            conn.close()

    async def bulk_document_operation(self, operation: BulkDocumentOperation, user_id: int) -> BulkOperationResult:
        """Perform bulk operations on documents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        successful_ids = []
        failed_ids = []
        errors = {}

        try:
            for doc_id in operation.document_ids:
                try:
                    if operation.operation == "delete":
                        cursor.execute("DELETE FROM editor_documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
                    elif operation.operation == "archive":
                        cursor.execute("UPDATE editor_documents SET status = 'archived' WHERE id = ? AND user_id = ?", (doc_id, user_id))
                    elif operation.operation == "publish":
                        cursor.execute("UPDATE editor_documents SET status = 'published' WHERE id = ? AND user_id = ?", (doc_id, user_id))
                    
                    if cursor.rowcount > 0:
                        successful_ids.append(doc_id)
                    else:
                        failed_ids.append(doc_id)
                        errors[doc_id] = "Document not found or access denied"
                        
                except Exception as e:
                    failed_ids.append(doc_id)
                    errors[doc_id] = str(e)
            
            conn.commit()
            
            return BulkOperationResult(
                successful_ids=successful_ids,
                failed_ids=failed_ids,
                errors=errors,
                total_processed=len(operation.document_ids)
            )
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    async def check_database_health(self) -> bool:
        """Check database connectivity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM editor_documents")
            conn.close()
            return True
        except:
            return False

    # Helper methods
    def _calculate_word_count(self, content: str) -> int:
        """Calculate word count"""
        if not content:
            return 0
        words = content.strip().split()
        return len([word for word in words if word])

    def _calculate_reading_time(self, word_count: int) -> int:
        """Calculate reading time in minutes (200 words per minute)"""
        return max(1, (word_count + 199) // 200)  # Round up

    def _row_to_document_response(self, row) -> EditorDocumentResponse:
        """Convert database row to document response"""
        return EditorDocumentResponse(
            id=row['id'],
            user_id=row['user_id'],
            title=row['title'],
            content=row['content'],
            template_id=row['template_id'],
            document_type=row['document_type'],
            status=row['status'],
            version=row['version'],
            word_count=row['word_count'],
            reading_time=row['reading_time'],
            metadata=json.loads(row['metadata']) if row['metadata'] else None,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_document_summary(self, row) -> EditorDocumentSummary:
        """Convert database row to document summary"""
        return EditorDocumentSummary(
            id=row['id'],
            title=row['title'],
            document_type=row['document_type'],
            status=row['status'],
            word_count=row['word_count'],
            reading_time=row['reading_time'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    async def _create_document_version(self, document_id: int, content: str, change_summary: str):
        """Create a document version entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current version number
            cursor.execute("SELECT MAX(version) FROM editor_document_versions WHERE document_id = ?", (document_id,))
            max_version = cursor.fetchone()[0] or 0
            
            # Insert new version
            cursor.execute("""
                INSERT INTO editor_document_versions 
                (document_id, version_number, content, change_summary)
                VALUES (?, ?, ?, ?)
            """, (document_id, max_version + 1, content, change_summary))
            
            conn.commit()
            
        finally:
            conn.close()