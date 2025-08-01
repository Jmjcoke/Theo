"""
Template Service
Handles document template management and operations
"""

import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.editor_models import *


class TemplateService:
    def __init__(self):
        self.db_path = "theo.db"

    async def list_templates(
        self, 
        user_id: int, 
        document_type: Optional[DocumentType] = None
    ) -> List[EditorTemplateSummary]:
        """List available templates (system + user templates)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, name, description, document_type, is_system 
                FROM editor_templates 
                WHERE is_system = 1 OR created_by = ?
            """
            params = [user_id]
            
            if document_type:
                query += " AND document_type = ?"
                params.append(document_type)
                
            query += " ORDER BY is_system DESC, name ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [EditorTemplateSummary(**dict(row)) for row in rows]
            
        finally:
            conn.close()

    async def get_template(self, template_id: str, user_id: int) -> Optional[EditorTemplateResponse]:
        """Get a specific template"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM editor_templates 
                WHERE id = ? AND (is_system = 1 OR created_by = ?)
            """, (template_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Parse metadata if it exists
            template_data = dict(row)
            if template_data['metadata']:
                template_data['metadata'] = json.loads(template_data['metadata'])
            
            return EditorTemplateResponse(**template_data)
            
        finally:
            conn.close()

    async def create_template(self, template: CreateEditorTemplate, user_id: int) -> EditorTemplateResponse:
        """Create a custom user template"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            template_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO editor_templates 
                (id, name, description, template_content, document_type, is_system, created_by, metadata)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """, (
                template_id, template.name, template.description,
                template.template_content, template.document_type, user_id,
                json.dumps(template.metadata) if template.metadata else None
            ))
            
            conn.commit()
            
            # Return the created template
            return await self.get_template(template_id, user_id)
            
        finally:
            conn.close()

    async def update_template(
        self, 
        template_id: str, 
        template: CreateEditorTemplate, 
        user_id: int
    ) -> Optional[EditorTemplateResponse]:
        """Update a user template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Verify user owns this template
            cursor.execute("""
                SELECT id FROM editor_templates 
                WHERE id = ? AND created_by = ? AND is_system = 0
            """, (template_id, user_id))
            
            if not cursor.fetchone():
                return None
            
            # Update the template
            cursor.execute("""
                UPDATE editor_templates 
                SET name = ?, description = ?, template_content = ?, 
                    document_type = ?, metadata = ?
                WHERE id = ?
            """, (
                template.name, template.description, template.template_content,
                template.document_type, 
                json.dumps(template.metadata) if template.metadata else None,
                template_id
            ))
            
            conn.commit()
            
            # Return updated template
            return await self.get_template(template_id, user_id)
            
        finally:
            conn.close()

    async def delete_template(self, template_id: str, user_id: int) -> bool:
        """Delete a user template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM editor_templates 
                WHERE id = ? AND created_by = ? AND is_system = 0
            """, (template_id, user_id))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
            
        finally:
            conn.close()

    async def duplicate_template(
        self, 
        template_id: str, 
        new_name: str, 
        user_id: int
    ) -> Optional[EditorTemplateResponse]:
        """Duplicate an existing template"""
        # Get the original template
        original = await self.get_template(template_id, user_id)
        if not original:
            return None
        
        # Create new template based on original
        new_template = CreateEditorTemplate(
            name=new_name,
            description=f"Copy of {original.name}",
            template_content=original.template_content,
            document_type=original.document_type,
            metadata=original.metadata
        )
        
        return await self.create_template(new_template, user_id)

    async def get_template_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """Get template usage statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Usage by template
            cursor.execute("""
                SELECT 
                    t.id, t.name, 
                    COUNT(d.id) as usage_count,
                    MAX(d.created_at) as last_used
                FROM editor_templates t
                LEFT JOIN editor_documents d ON t.id = d.template_id AND d.user_id = ?
                WHERE t.is_system = 1 OR t.created_by = ?
                GROUP BY t.id, t.name
                ORDER BY usage_count DESC, t.name ASC
            """, (user_id, user_id))
            
            template_usage = [dict(row) for row in cursor.fetchall()]
            
            # Most popular template
            most_popular = template_usage[0] if template_usage and template_usage[0]['usage_count'] > 0 else None
            
            # Template type distribution
            cursor.execute("""
                SELECT 
                    t.document_type,
                    COUNT(d.id) as usage_count
                FROM editor_templates t
                LEFT JOIN editor_documents d ON t.id = d.template_id AND d.user_id = ?
                WHERE t.is_system = 1 OR t.created_by = ?
                GROUP BY t.document_type
            """, (user_id, user_id))
            
            type_distribution = {row['document_type']: row['usage_count'] for row in cursor.fetchall()}
            
            return {
                'template_usage': template_usage,
                'most_popular_template': most_popular,
                'type_distribution': type_distribution,
                'total_user_templates': len([t for t in template_usage if not t.get('is_system', True)])
            }
            
        finally:
            conn.close()

    async def search_templates(
        self, 
        query: str, 
        user_id: int, 
        document_type: Optional[DocumentType] = None
    ) -> List[EditorTemplateSummary]:
        """Search templates by name or description"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            search_query = """
                SELECT id, name, description, document_type, is_system 
                FROM editor_templates 
                WHERE (is_system = 1 OR created_by = ?)
                AND (name LIKE ? OR description LIKE ?)
            """
            params = [user_id, f"%{query}%", f"%{query}%"]
            
            if document_type:
                search_query += " AND document_type = ?"
                params.append(document_type)
                
            search_query += " ORDER BY is_system DESC, name ASC"
            
            cursor.execute(search_query, params)
            rows = cursor.fetchall()
            
            return [EditorTemplateSummary(**dict(row)) for row in rows]
            
        finally:
            conn.close()

    async def apply_template_to_document(
        self, 
        template_id: str, 
        document_id: int, 
        user_id: int,
        variables: Optional[Dict[str, str]] = None
    ) -> bool:
        """Apply a template to an existing document"""
        # Get template
        template = await self.get_template(template_id, user_id)
        if not template:
            return False
        
        # Process template content with variables
        content = template.template_content
        if variables:
            for key, value in variables.items():
                placeholder = f"[{key}]"
                content = content.replace(placeholder, value)
        
        # Update document
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE editor_documents 
                SET content = ?, template_id = ?, document_type = ?
                WHERE id = ? AND user_id = ?
            """, (content, template_id, template.document_type, document_id, user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
            
        finally:
            conn.close()

    async def get_template_variables(self, template_id: str, user_id: int) -> List[str]:
        """Extract variables from template content"""
        template = await self.get_template(template_id, user_id)
        if not template:
            return []
        
        import re
        # Find all placeholders in format [variable_name]
        variables = re.findall(r'\[([^\]]+)\]', template.template_content)
        return list(set(variables))  # Remove duplicates

    async def get_system_templates(self) -> List[EditorTemplateSummary]:
        """Get all system templates"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, description, document_type, is_system 
                FROM editor_templates 
                WHERE is_system = 1
                ORDER BY document_type, name
            """)
            
            rows = cursor.fetchall()
            return [EditorTemplateSummary(**dict(row)) for row in rows]
            
        finally:
            conn.close()

    async def backup_user_templates(self, user_id: int) -> Dict[str, Any]:
        """Create a backup of user's custom templates"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM editor_templates 
                WHERE created_by = ? AND is_system = 0
            """, (user_id,))
            
            templates = []
            for row in cursor.fetchall():
                template_data = dict(row)
                if template_data['metadata']:
                    template_data['metadata'] = json.loads(template_data['metadata'])
                templates.append(template_data)
            
            return {
                'user_id': user_id,
                'backup_date': datetime.utcnow().isoformat(),
                'template_count': len(templates),
                'templates': templates
            }
            
        finally:
            conn.close()

    async def restore_user_templates(self, backup_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Restore user templates from backup"""
        if backup_data.get('user_id') != user_id:
            raise ValueError("Backup data does not belong to this user")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        restored_count = 0
        failed_count = 0
        errors = []

        try:
            for template_data in backup_data.get('templates', []):
                try:
                    # Generate new ID to avoid conflicts
                    new_id = str(uuid.uuid4())
                    
                    cursor.execute("""
                        INSERT INTO editor_templates 
                        (id, name, description, template_content, document_type, is_system, created_by, metadata)
                        VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                    """, (
                        new_id,
                        template_data['name'],
                        template_data.get('description'),
                        template_data['template_content'],
                        template_data['document_type'],
                        user_id,
                        json.dumps(template_data['metadata']) if template_data.get('metadata') else None
                    ))
                    
                    restored_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Failed to restore template '{template_data.get('name', 'Unknown')}': {str(e)}")
            
            conn.commit()
            
            return {
                'restored_count': restored_count,
                'failed_count': failed_count,
                'errors': errors
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    async def check_health(self) -> bool:
        """Check template service health"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM editor_templates WHERE is_system = 1")
            system_template_count = cursor.fetchone()[0]
            conn.close()
            
            # Should have at least 5 system templates
            return system_template_count >= 5
            
        except Exception:
            return False

    async def get_template_preview(self, template_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a preview of template with sample content"""
        template = await self.get_template(template_id, user_id)
        if not template:
            return None
        
        # Generate preview with sample variables
        sample_variables = {
            'Sermon Title': 'The Power of Faith',
            'Scripture Reference': 'Hebrews 11:1',
            'Paper Title': 'Theological Perspectives on Grace',
            'Author': 'John Doe',
            'Institution': 'Seminary College',
            'Date': datetime.now().strftime('%B %d, %Y'),
            'Article Title': 'Understanding Biblical Hermeneutics',
            'Lesson Title': 'The Parable of the Good Samaritan',
            'Devotional Title': 'Walking in His Light'
        }
        
        preview_content = template.template_content
        for key, value in sample_variables.items():
            placeholder = f"[{key}]"
            preview_content = preview_content.replace(placeholder, value)
        
        return {
            'template_id': template_id,
            'name': template.name,
            'document_type': template.document_type,
            'preview_content': preview_content[:1000] + "..." if len(preview_content) > 1000 else preview_content,
            'word_count': len(preview_content.split()),
            'variables_found': await self.get_template_variables(template_id, user_id)
        }