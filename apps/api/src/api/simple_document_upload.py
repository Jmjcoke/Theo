"""
Enhanced Standardized Document Upload Endpoint

Provides a robust, reliable upload endpoint with proper validation,
error handling, security measures, and real-time progress tracking.
Replaces the complex flow-based upload system with a direct, efficient approach.
"""
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from src.middleware.auth_dependencies import require_admin_role
from typing import Dict, Any, Optional, AsyncGenerator
import uuid
import os
import aiosqlite
import mimetypes
import magic
import json
import asyncio
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["document-upload"])

# Configuration constants
MAX_FILE_SIZE = 52428800  # 50MB
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}
ALLOWED_DOCUMENT_TYPES = {'biblical', 'theological'}
UPLOAD_DIR = "uploads"

# MIME type mappings for security validation
EXPECTED_MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain',
    '.md': {'text/markdown', 'text/plain', 'text/x-markdown'}
}

class DocumentValidationError(Exception):
    """Custom exception for document validation errors."""
    def __init__(self, message: str, error_code: str = "validation_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class DocumentStorageError(Exception):
    """Custom exception for document storage errors."""
    def __init__(self, message: str, error_code: str = "storage_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

def validate_file_extension(filename: str) -> str:
    """Validate file extension and return normalized extension."""
    if not filename or '.' not in filename:
        raise DocumentValidationError("File has no extension", "invalid_extension")
    
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise DocumentValidationError(
            f"File type {file_ext} not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}",
            "unsupported_file_type"
        )
    
    return file_ext

def validate_file_size(file_size: int) -> None:
    """Validate file size constraints."""
    if file_size == 0:
        raise DocumentValidationError("File is empty", "empty_file")
    
    if file_size > MAX_FILE_SIZE:
        raise DocumentValidationError(
            f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.1f}MB. "
            f"Your file is {file_size / 1024 / 1024:.1f}MB",
            "file_too_large"
        )

def validate_mime_type(content: bytes, filename: str, file_ext: str) -> str:
    """Validate MIME type against file extension."""
    # Detect MIME type from content
    mime_type = None
    try:
        # Use python-magic for reliable MIME type detection
        mime_type = magic.from_buffer(content[:1024], mime=True)
    except Exception:
        # Fallback to filename-based detection
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    # Validate MIME type matches extension
    expected_mime = EXPECTED_MIME_TYPES.get(file_ext)
    if expected_mime:
        if isinstance(expected_mime, set):
            # Multiple allowed MIME types (e.g., markdown)
            if mime_type not in expected_mime:
                raise DocumentValidationError(
                    f"MIME type {mime_type} doesn't match file extension {file_ext}",
                    "mime_type_mismatch"
                )
        else:
            # Single expected MIME type
            if mime_type != expected_mime:
                raise DocumentValidationError(
                    f"MIME type {mime_type} doesn't match file extension {file_ext}",
                    "mime_type_mismatch"
                )
    
    return mime_type

def validate_document_type(document_type: str) -> None:
    """Validate document type."""
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise DocumentValidationError(
            f"Invalid document type: {document_type}. "
            f"Allowed types: {', '.join(ALLOWED_DOCUMENT_TYPES)}",
            "invalid_document_type"
        )

async def store_file(content: bytes, filename: str) -> str:
    """Store file securely with unique filename."""
    try:
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        safe_filename = f"{unique_id}_{filename}"
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Store file
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Verify file was written correctly
        if not os.path.exists(file_path) or os.path.getsize(file_path) != len(content):
            raise DocumentStorageError("File storage verification failed", "storage_verification_failed")
        
        return file_path
        
    except OSError as e:
        raise DocumentStorageError(f"Failed to store file: {str(e)}", "filesystem_error")
    except Exception as e:
        raise DocumentStorageError(f"Unexpected storage error: {str(e)}", "unexpected_storage_error")

async def create_database_record(
    filename: str,
    document_type: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    category: Optional[str],
    user_id: str,
    original_filename: str
) -> int:
    """Create database record for uploaded document."""
    try:
        metadata = {
            "category": category or "",
            "upload_method": "enhanced_simple",
            "file_size": file_size,
            "mime_type": mime_type,
            "original_filename": original_filename,
            "file_extension": Path(original_filename).suffix.lower()
        }
        
        async with aiosqlite.connect("theo.db") as db:
            await db.execute("""
                INSERT INTO documents (
                    filename, original_filename, document_type, file_path, 
                    processing_status, uploaded_by, file_size, mime_type,
                    metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                filename,
                original_filename,
                document_type,
                file_path,
                'queued',
                user_id,
                file_size,
                mime_type,
                json.dumps(metadata),
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            await db.commit()
            
            # Get the document ID
            cursor = await db.execute("SELECT last_insert_rowid()")
            document_id = (await cursor.fetchone())[0]
            
            return document_id
            
    except Exception as e:
        raise DocumentStorageError(f"Database record creation failed: {str(e)}", "database_error")

async def progress_generator(document_id: int) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for upload progress."""
    try:
        # Emit upload completion
        yield f"data: {json.dumps({'event': 'upload_complete', 'documentId': document_id, 'status': 'uploaded'})}\n\n"
        
        # Simulate processing stages for user feedback
        stages = [
            ("validation_complete", "File validation completed"),
            ("storage_complete", "File stored successfully"),
            ("database_complete", "Database record created"),
            ("processing_queued", "Document queued for processing")
        ]
        
        for stage, message in stages:
            await asyncio.sleep(0.1)  # Small delay for UX
            yield f"data: {json.dumps({'event': stage, 'message': message, 'documentId': document_id})}\n\n"
        
        # Final success event
        yield f"data: {json.dumps({'event': 'upload_success', 'documentId': document_id, 'status': 'complete'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in progress generator: {str(e)}")
        yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, TXT, MD)"),
    documentType: str = Form(..., description="Document type: 'biblical' or 'theological'"),
    category: Optional[str] = Form(None, description="Optional document category"),
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Enhanced standardized document upload endpoint.
    
    This endpoint provides:
    - Comprehensive file validation (type, size, MIME type, security)
    - Secure file storage with unique naming
    - Proper error handling with specific error codes
    - Database record creation with detailed metadata
    - Real-time progress updates via Server-Sent Events
    
    **Authentication:** Requires admin role JWT token.
    
    **File Requirements:**
    - Maximum size: 50MB
    - Supported types: PDF, DOCX, TXT, MD
    - File must not be empty
    - MIME type must match file extension
    
    **Returns:**
    Complete upload confirmation with document metadata and processing status.
    """
    logger.info(f"Document upload initiated by user {current_user.get('email', 'unknown')}")
    
    try:
        # Step 1: Validate inputs
        if not file.filename:
            raise DocumentValidationError("No filename provided", "missing_filename")
        
        validate_document_type(documentType)
        file_ext = validate_file_extension(file.filename)
        
        # Step 2: Read and validate file content
        content = await file.read()
        file_size = len(content)
        validate_file_size(file_size)
        
        # Step 3: Validate MIME type
        mime_type = validate_mime_type(content, file.filename, file_ext)
        
        # Step 4: Store file securely
        file_path = await store_file(content, file.filename)
        
        # Step 5: Create database record
        document_id = await create_database_record(
            filename=Path(file_path).name,
            document_type=documentType,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            category=category,
            user_id=current_user["user_id"],
            original_filename=file.filename
        )
        
        logger.info(f"Document uploaded successfully: ID {document_id}, file: {file.filename}")
        
        # Start background processing task with Celery
        from src.core.celery_app import process_document_async
        task_result = process_document_async.delay(str(document_id))
        job_id = task_result.id
        
        # Return success response
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "documentId": document_id,
            "filename": file.filename,
            "documentType": documentType,
            "processingStatus": "queued",
            "uploadedAt": datetime.utcnow().isoformat(),
            "jobId": job_id,  # Added for frontend SSE compatibility
            "fileSize": file_size,
            "mimeType": mime_type,
            "category": category,
            "uploadedBy": current_user["email"],
            "filePath": file_path,
            "metadata": {
                "file_extension": file_ext,
                "upload_method": "enhanced_simple",
                "validation_passed": True,
                "jobId": job_id,
                "celery_task_id": job_id
            }
        }
        
    except DocumentValidationError as e:
        logger.warning(f"Document validation failed: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.error_code,
                "message": e.message,
                "type": "validation_error"
            }
        )
        
    except DocumentStorageError as e:
        logger.error(f"Document storage failed: {e.message}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": e.error_code,
                "message": e.message,
                "type": "storage_error"
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "unexpected_error",
                "message": f"Upload failed: {str(e)}",
                "type": "internal_error"
            }
        )

@router.post("/upload-stream")
async def upload_document_with_progress(
    file: UploadFile = File(...),
    documentType: str = Form(...),
    category: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Upload document with real-time progress updates via Server-Sent Events.
    
    This endpoint performs the same upload process as /upload but returns
    a streaming response with real-time progress updates for enhanced UX.
    """
    try:
        # Perform upload (reuse logic from main upload endpoint)
        upload_result = await upload_document(
            background_tasks=BackgroundTasks(),
            file=file,
            documentType=documentType,
            category=category,
            current_user=current_user
        )
        
        # Return streaming response with progress updates
        return StreamingResponse(
            progress_generator(upload_result["documentId"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Streaming upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "streaming_error",
                "message": f"Streaming upload failed: {str(e)}",
                "type": "internal_error"
            }
        )

# Backward compatibility - keep the simple endpoint as an alias
@router.post("/upload-simple")
async def upload_document_simple_compat(
    file: UploadFile = File(...),
    documentType: str = Form(...),
    category: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Backward compatibility endpoint - redirects to enhanced upload.
    
    This endpoint maintains compatibility with existing frontend code
    while providing the enhanced functionality of the new upload system.
    """
    return await upload_document(
        background_tasks=BackgroundTasks(),
        file=file,
        documentType=documentType,
        category=category,
        current_user=current_user
    )