# Dev Notes

## Relevant Source Tree Info
Based on PocketFlow-first architecture in `apps/api/`:
- Main application: `apps/api/main.py` - Add document upload routes here
- Node directory: `apps/api/src/nodes/documents/` - Create upload nodes here
- Flow directory: `apps/api/src/flows/` - Create DocumentUploadFlow here
- API routes: `apps/api/src/api/` - Create document upload endpoint here
- Database schema: `apps/api/database/supabase_schema.sql` - Verify documents table
- Environment config: `apps/api/src/core/config.py` - Add file upload settings

## Architecture Integration Points
From Epic 3 context and previous Story 3.1 completion:
- **Queue System**: Uses existing Celery/Redis setup from Story 3.1
- **Background Processing**: Document upload will dispatch jobs to existing queue infrastructure
- **Real-time Updates**: Story 3.4 will monitor job progress via existing queue status endpoints

## Database Schema Requirements
**Documents Table Structure** (from architecture specs):
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('biblical', 'theological')),
    processing_status VARCHAR(50) NOT NULL DEFAULT 'queued' CHECK (processing_status IN ('queued', 'processing', 'completed', 'failed')),
    uploaded_by UUID NOT NULL REFERENCES users(id),
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## File Upload Configuration Requirements
**File Storage Strategy**:
- **Development**: Local file storage in `uploads/` directory
- **Production**: File storage path configurable via environment
- **File Types**: PDF, DOCX, TXT, MD only
- **Size Limits**: Maximum 50MB per file
- **Security**: Validate file types, scan for malicious content

## API Endpoint Specification
**Endpoint**: `POST /api/admin/upload`
**Authentication**: Requires 'admin' role JWT token
**Content-Type**: `multipart/form-data`
**Request Body**:
```
file: <uploaded_file>
documentType: "biblical" | "theological"
category: <optional_string>
```
**Response Format**:
```json
{
  "documentId": "uuid",
  "filename": "original_filename.pdf",
  "documentType": "biblical",
  "processingStatus": "queued",
  "uploadedAt": "2025-07-23T10:30:00Z",
  "jobId": "celery_job_uuid"
}
```

## Environment Variables Needed
```bash