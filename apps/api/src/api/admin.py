"""
Admin API Routes for Theo

FastAPI router for admin-only endpoints including dashboard metrics,
user management, and system administration.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from databases import Database
from src.middleware.auth_dependencies import require_admin_role
from src.admin.analytics import DashboardAnalytics
from src.admin.configuration import ConfigurationManager, SystemHealthChecker
from src.core.config import settings
from src.models.configuration_models import (
    ConfigurationUpdate,
    SystemConfigurationResponse,
    SystemHealth,
    ConfigurationValidationError
)
from datetime import datetime
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter()
logger = logging.getLogger(__name__)


# Temporary route without authentication for testing
@router.get("/admin/dashboard/test")
async def get_dashboard_test() -> Dict[str, Any]:
    """
    Temporary dashboard metrics endpoint without authentication for testing.
    
    Returns basic metrics for testing frontend connectivity.
    """
    return {
        "users": {
            "total": 5,
            "pending": 2,
            "approved": 3
        },
        "documents": {
            "total": 10,
            "processing": 1,
            "completed": 8,
            "failed": 1
        },
        "system": {
            "uptime": "Running",
            "version": "1.0.0",
            "lastBackup": "2025-01-27T00:00:00Z"
        }
    }


@router.get("/admin/documents/test")
async def get_documents_test() -> Dict[str, Any]:
    """
    Temporary documents list endpoint without authentication for testing.
    
    Returns sample documents for testing frontend connectivity.
    """
    return {
        "documents": [
            {
                "id": "1",
                "filename": "bible_study.pdf",
                "document_type": "biblical",
                "processing_status": "completed",
                "uploaded_by": "admin@example.com",
                "uploaded_at": "2025-01-27T10:00:00Z",
                "processed_at": "2025-01-27T10:05:00Z",
                "chunk_count": 45,
                "metadata": {"pages": 12, "size": "2.5MB"}
            },
            {
                "id": "2", 
                "filename": "theology_notes.docx",
                "document_type": "theological",
                "processing_status": "processing",
                "uploaded_by": "admin@example.com",
                "uploaded_at": "2025-01-27T11:00:00Z",
                "chunk_count": None,
                "metadata": {"pages": 8, "size": "1.2MB"}
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 2,
            "pages": 1
        }
    }


@router.get("/admin/settings/test")
async def get_settings_test() -> Dict[str, Any]:
    """
    Temporary settings endpoint without authentication for testing.
    
    Returns sample system settings for testing frontend connectivity.
    """
    return {
        "configurations": {
            "upload": {
                "max_file_size_biblical": 50,  # MB
                "max_file_size_theological": 50,  # MB
                "allowed_extensions": [".pdf", ".docx", ".txt"],
                "max_daily_uploads": 100
            },
            "system": {
                "maintenance_mode": False,
                "backup_enabled": True,
                "backup_frequency": "daily",
                "system_version": "1.0.0"
            },
            "processing": {
                "max_concurrent_jobs": 5,
                "job_timeout_minutes": 30,
                "retry_attempts": 3
            }
        }
    }


@router.get("/admin/debug/database")
async def debug_database_connection(
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    Debug endpoint to test database connection.
    """
    try:
        import aiosqlite
        import os
        
        database_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
        
        async with aiosqlite.connect(database_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Test basic connection
            cursor = await db.execute("SELECT 1 as test")
            test_result = await cursor.fetchone()
            
            # Count documents
            cursor = await db.execute("SELECT COUNT(*) as count FROM documents")
            doc_count = await cursor.fetchone()
            
            return {
                "status": "success",
                "database_path": database_path,
                "connection_test": dict(test_result) if test_result else None,
                "document_count": dict(doc_count) if doc_count else None,
                "user": current_user
            }
            
    except Exception as e:
        logger.error(f"Database debug failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "user": current_user
        }


@router.get("/admin/debug/documents")
async def debug_documents_query(
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    Debug endpoint to test documents query without Pydantic models.
    """
    try:
        import aiosqlite
        import os
        
        database_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
        
        async with aiosqlite.connect(database_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Execute the same query as the documents endpoint
            cursor = await db.execute("""
                SELECT id, filename, document_type, processing_status, 
                       created_at as uploaded_at, updated_at as processed_at,
                       file_path
                FROM documents
                ORDER BY created_at DESC LIMIT 20 OFFSET 0
            """)
            documents_result = await cursor.fetchall()
            
            # Convert to simple dicts
            documents = []
            for row in documents_result:
                doc_dict = dict(row)
                documents.append({
                    "id": str(doc_dict["id"]),
                    "filename": doc_dict["filename"],
                    "document_type": doc_dict["document_type"],
                    "processing_status": doc_dict["processing_status"],
                    "uploaded_at": doc_dict["uploaded_at"],
                    "processed_at": doc_dict["processed_at"]
                })
            
            return {
                "status": "success",
                "documents": documents,
                "count": len(documents),
                "user": current_user
            }
            
    except Exception as e:
        logger.error(f"Documents debug failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "user": current_user
        }


# Pydantic Models for User Management
class UserUpdateRequest(BaseModel):
    status: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    created_at: str
    last_login_at: Optional[str] = None


class UserListResponse(BaseModel):
    users: List[UserResponse]
    pagination: Dict[str, Any]


class UserDeleteResponse(BaseModel):
    message: str
    user_id: str
    deleted_at: str


# Pydantic Models for Document Management
class DocumentResponse(BaseModel):
    id: str
    filename: str
    document_type: str  # "biblical" | "theological"
    processing_status: str  # "queued" | "processing" | "completed" | "failed"
    uploaded_by: str
    uploaded_at: str
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    chunk_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    pagination: Dict[str, Any]


class DocumentDeleteResponse(BaseModel):
    message: str
    document_id: str
    deleted_at: str


@router.get("/admin/documents", response_model=DocumentListResponse)
async def get_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by processing status"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> DocumentListResponse:
    """
    Get paginated list of documents with optional filtering.
    
    Requires admin role authentication. Returns documents with pagination info.
    """
    try:
        import aiosqlite
        import os
        import json
        
        database_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
        
        async with aiosqlite.connect(database_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Build WHERE clause for filtering
            where_conditions = []
            query_params = []
            
            if status:
                where_conditions.append("processing_status = ?")
                query_params.append(status)
            
            if document_type:
                where_conditions.append("document_type = ?")
                query_params.append(document_type)
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Count total documents
            count_query = f"SELECT COUNT(*) as total FROM documents{where_clause}"
            cursor = await db.execute(count_query, query_params)
            total_result = await cursor.fetchone()
            total = total_result["total"] if total_result else 0
            
            # Calculate pagination
            offset = (page - 1) * limit
            total_pages = (total + limit - 1) // limit
            
            # Get documents with pagination
            documents_query = f"""
                SELECT id, filename, document_type, processing_status, 
                       uploaded_by, created_at as uploaded_at, updated_at as processed_at,
                       error_message, chunk_count, metadata
                FROM documents{where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            
            cursor = await db.execute(documents_query, query_params + [limit, offset])
            documents_result = await cursor.fetchall()
            
            # Transform results
            documents = []
            for row in documents_result:
                doc_dict = dict(row)
                
                # Parse metadata if it's a string
                metadata = doc_dict.get("metadata")
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                
                documents.append(DocumentResponse(
                    id=str(doc_dict["id"]),
                    filename=doc_dict["filename"],
                    document_type=doc_dict["document_type"],
                    processing_status=doc_dict["processing_status"],
                    uploaded_by=doc_dict["uploaded_by"] or "system",
                    uploaded_at=doc_dict["uploaded_at"],
                    processed_at=doc_dict["processed_at"],
                    error_message=doc_dict.get("error_message"),
                    chunk_count=doc_dict.get("chunk_count"),
                    metadata=metadata
                ))
            
            return DocumentListResponse(
                documents=documents,
                pagination={
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": total_pages
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch documents")


@router.get("/admin/documents/test", response_model=DocumentListResponse)
async def get_documents_test(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by processing status"),
    document_type: Optional[str] = Query(None, description="Filter by document type")
) -> DocumentListResponse:
    """
    Test endpoint for documents without authentication.
    """
    try:
        import aiosqlite
        import os
        import json
        
        database_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
        
        async with aiosqlite.connect(database_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Build WHERE clause for filtering
            where_conditions = []
            query_params = []
            
            if status:
                where_conditions.append("processing_status = ?")
                query_params.append(status)
            
            if document_type:
                where_conditions.append("document_type = ?")
                query_params.append(document_type)
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Count total documents
            count_query = f"SELECT COUNT(*) as total FROM documents{where_clause}"
            cursor = await db.execute(count_query, query_params)
            total_result = await cursor.fetchone()
            total = total_result["total"] if total_result else 0
            
            # Calculate pagination
            offset = (page - 1) * limit
            total_pages = (total + limit - 1) // limit
            
            # Get documents with pagination
            documents_query = f"""
                SELECT id, filename, document_type, processing_status, 
                       uploaded_by, created_at as uploaded_at, updated_at as processed_at,
                       error_message, chunk_count, metadata
                FROM documents{where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            
            cursor = await db.execute(documents_query, query_params + [limit, offset])
            documents_result = await cursor.fetchall()
            
            # Transform results
            documents = []
            for row in documents_result:
                doc_dict = dict(row)
                
                # Parse metadata if it's a string
                metadata = doc_dict.get("metadata")
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                
                documents.append(DocumentResponse(
                    id=str(doc_dict["id"]),
                    filename=doc_dict["filename"],
                    document_type=doc_dict["document_type"],
                    processing_status=doc_dict["processing_status"],
                    uploaded_by=doc_dict["uploaded_by"] or "system",
                    uploaded_at=doc_dict["uploaded_at"],
                    processed_at=doc_dict["processed_at"],
                    error_message=doc_dict.get("error_message"),
                    chunk_count=doc_dict.get("chunk_count"),
                    metadata=metadata
                ))
            
            return DocumentListResponse(
                documents=documents,
                pagination={
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": total_pages
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch documents")


@router.get("/admin/dashboard/metrics")
async def get_dashboard_metrics(
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    Get dashboard metrics for admin dashboard.
    
    Requires admin role authentication. Returns comprehensive metrics
    including user counts, document processing statistics, and system status.
    
    Returns:
        Dict containing dashboard metrics with users, documents, and system data
    """
    try:
        logger.info(f"Admin dashboard metrics requested by user: {current_user.get('user_id', 'unknown')}")
        
        # Import aiosqlite for direct database access
        import aiosqlite
        import os
        
        # Use the same database path as other parts of the application
        database_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
        
        async with aiosqlite.connect(database_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get user counts by status using standard SQL queries
            cursor = await db.execute("SELECT COUNT(*) as count FROM users")
            total_users_result = await cursor.fetchone()
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM users WHERE status = ?", ("pending",))
            pending_users_result = await cursor.fetchone()
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM users WHERE status = ?", ("approved",))
            approved_users_result = await cursor.fetchone()
            
            # Get document counts by status
            cursor = await db.execute("SELECT COUNT(*) as count FROM documents")
            total_docs_result = await cursor.fetchone()
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM documents WHERE processing_status = ?", ("processing",))
            processing_docs_result = await cursor.fetchone()
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM documents WHERE processing_status = ?", ("completed",))
            completed_docs_result = await cursor.fetchone()
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM documents WHERE processing_status = ?", ("failed",))
            failed_docs_result = await cursor.fetchone()
            
            # Create metrics response
            metrics = {
                "users": {
                    "total": total_users_result["count"] if total_users_result else 0,
                    "pending": pending_users_result["count"] if pending_users_result else 0,
                    "approved": approved_users_result["count"] if approved_users_result else 0
                },
                "documents": {
                    "total": total_docs_result["count"] if total_docs_result else 0,
                    "processing": processing_docs_result["count"] if processing_docs_result else 0,
                    "completed": completed_docs_result["count"] if completed_docs_result else 0,
                    "failed": failed_docs_result["count"] if failed_docs_result else 0
                },
                "system": {
                    "uptime": "Running",
                    "version": "1.0.0",
                    "lastBackup": "N/A"
                }
            }
        
        logger.info(f"Dashboard metrics retrieved successfully for admin: {current_user.get('user_id', 'unknown')}")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to retrieve dashboard metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard metrics: {str(e)}"
        )


@router.get("/admin/dashboard/activity")
async def get_dashboard_activity(
    current_user: Dict[str, Any] = Depends(require_admin_role),
    days: int = 7
) -> Dict[str, Any]:
    """
    Get recent activity summary for admin dashboard.
    
    Args:
        days: Number of days to look back for activity (default: 7)
    
    Returns:
        Dict containing recent user and document activity statistics
    """
    database = None
    
    try:
        logger.info(f"Admin activity summary requested by user: {current_user['user_id']} for {days} days")
        
        # Validate days parameter
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=400,
                detail="Days parameter must be between 1 and 365"
            )
        
        # Create database connection
        database = Database(settings.database_url)
        await database.connect()
        
        # Create analytics instance and collect activity data
        analytics = DashboardAnalytics(database=database)
        
        user_activity = await analytics.get_user_activity_summary(days=days)
        document_activity = await analytics.get_document_processing_summary(days=days)
        
        result = {
            "user_activity": user_activity,
            "document_activity": document_activity,
            "period_days": days
        }
        
        logger.info(f"Activity summary retrieved successfully for admin: {current_user['user_id']}")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve activity summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve activity summary: {str(e)}"
        )
    
    finally:
        # Ensure database connection is closed
        if database:
            await database.disconnect()


@router.get("/admin/health")
async def admin_health_check(
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    Admin-only health check endpoint.
    
    Tests admin authentication and basic system connectivity.
    Useful for monitoring admin access and system status.
    
    Returns:
        Dict with health status and admin user information
    """
    try:
        logger.info(f"Admin health check requested by user: {current_user['user_id']}")
        
        return {
            "status": "healthy",
            "service": "admin-api",
            "admin_user": {
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "role": current_user["role"]
            },
            "timestamp": "2025-01-27T00:00:00Z"  # Placeholder for actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Admin health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Admin health check failed: {str(e)}"
        )


@router.get("/admin/system/status")
async def get_system_status(
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    Get detailed system status information.
    
    Returns comprehensive system health including database connectivity,
    service status, and configuration information.
    
    Returns:
        Dict with detailed system status information
    """
    database = None
    
    try:
        logger.info(f"System status requested by admin: {current_user['user_id']}")
        
        # Test database connectivity
        database_status = "unknown"
        try:
            database = Database(settings.database_url)
            await database.connect()
            
            # Test a simple query
            test_result = await database.fetch_one("SELECT 1 as test")
            database_status = "connected" if test_result else "error"
            
        except Exception as db_error:
            logger.warning(f"Database connectivity test failed: {str(db_error)}")
            database_status = "disconnected"
        
        result = {
            "system": {
                "status": "operational" if database_status == "connected" else "degraded",
                "database": {
                    "status": database_status,
                    "url_configured": bool(settings.database_url)
                },
                "configuration": {
                    "app_version": getattr(settings, 'app_version', '1.0.0'),
                    "environment": getattr(settings, 'environment', 'development')
                }
            },
            "checked_by": current_user["user_id"],
            "timestamp": "2025-01-27T00:00:00Z"  # Placeholder
        }
        
        logger.info(f"System status retrieved successfully for admin: {current_user['user_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to retrieve system status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve system status: {str(e)}"
        )
    
    finally:
        # Ensure database connection is closed
        if database:
            await database.disconnect()


# User Management Endpoints

@router.get("/admin/users", response_model=UserListResponse)
async def get_users(
    current_user: Dict[str, Any] = Depends(require_admin_role),
    status: Optional[str] = Query(None, description="Filter users by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Users per page")
) -> UserListResponse:
    """
    Get list of users with optional status filtering.
    
    Args:
        status: Filter users by status (pending, approved, denied)
        page: Page number for pagination
        limit: Number of users per page
    
    Returns:
        UserListResponse with users and pagination info
    """
    try:
        logger.info(f"User list requested by admin: {current_user['user_id']} with status filter: {status}")
        
        # Import aiosqlite for direct database access
        import aiosqlite
        import os
        
        # Use the same database path as other parts of the application
        database_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
        
        async with aiosqlite.connect(database_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Calculate offset for pagination
            offset = (page - 1) * limit
            
            # Build query with optional status filter
            base_query = "SELECT id, email, role, status, created_at FROM users"
            count_query = "SELECT COUNT(*) as total FROM users"
            params = []
            
            if status:
                base_query += " WHERE status = ?"
                count_query += " WHERE status = ?"
                params.append(status)
            
            # Add pagination
            base_query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            query_params = params + [limit, offset]
            
            # Execute queries
            cursor = await db.execute(base_query, query_params)
            users_result = await cursor.fetchall()
            
            cursor = await db.execute(count_query, params)
            count_result = await cursor.fetchone()
            
            total_users = count_result["total"] if count_result else 0
            total_pages = (total_users + limit - 1) // limit
            
            # Format users
            users = []
            for row in users_result:
                users.append(UserResponse(
                    id=str(row["id"]),
                    email=row["email"],
                    role=row["role"],
                    status=row["status"],
                    created_at=str(row["created_at"]) if row["created_at"] else "",
                    last_login_at=None  # Not tracking login times yet
                ))
            
            pagination = {
                "page": page,
                "limit": limit,
                "total": total_users,
                "pages": total_pages
            }
            
            logger.info(f"Retrieved {len(users)} users for admin: {current_user['user_id']}")
            return UserListResponse(users=users, pagination=pagination)
        
    except Exception as e:
        logger.error(f"Failed to retrieve users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.patch("/admin/users/{user_id}")
async def update_user_status(
    user_id: str,
    user_update: UserUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    Update user status (approve/deny).
    
    Args:
        user_id: The ID of the user to update
        user_update: Request body with new status
    
    Returns:
        Success message with updated user info
    """
    database = None
    
    try:
        logger.info(f"User status update requested by admin: {current_user['user_id']} for user: {user_id}")
        
        # Validate status
        valid_statuses = ["pending", "approved", "denied"]
        if user_update.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Create database connection
        database = Database(settings.database_url)
        await database.connect()
        
        # Check if user exists
        user_check = await database.fetch_one(
            "SELECT id, email, status FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        
        if not user_check:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Update user status
        update_query = """
            UPDATE users 
            SET status = :status, updated_at = CURRENT_TIMESTAMP 
            WHERE id = :user_id 
            RETURNING id, email, status, updated_at
        """
        
        updated_user = await database.fetch_one(
            update_query,
            {"status": user_update.status, "user_id": user_id}
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=500,
                detail="Failed to update user status"
            )
        
        # Log the action for audit purposes
        logger.info(f"User {user_id} status updated to {user_update.status} by admin {current_user['user_id']}")
        
        return {
            "message": "User status updated successfully",
            "user": {
                "id": str(updated_user["id"]),
                "email": updated_user["email"],
                "status": updated_user["status"],
                "updated_at": updated_user["updated_at"].isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user status: {str(e)}"
        )
    
    finally:
        if database:
            await database.disconnect()


# Document Management Endpoints



@router.delete("/admin/documents/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> DocumentDeleteResponse:
    """
    Delete a document and its associated data.
    
    This endpoint triggers a PocketFlow workflow to:
    1. Delete document metadata from the database
    2. Clean up vector embeddings from Supabase
    3. Remove associated file storage
    
    Args:
        document_id: The ID of the document to delete
    
    Returns:
        DocumentDeleteResponse with deletion confirmation
    """
    database = None
    
    try:
        logger.info(f"Document deletion requested by admin: {current_user['user_id']} for document: {document_id}")
        
        # Create database connection
        database = Database(settings.database_url)
        await database.connect()
        
        # Check if document exists
        document_check = await database.fetch_one(
            "SELECT id, filename FROM documents WHERE id = :document_id",
            {"document_id": document_id}
        )
        
        if not document_check:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        # Import and run the document deletion flow
        from src.flows.document_deletion_flow import DocumentDeletionFlow
        
        # Prepare shared data for the flow
        shared = {"document_id": document_id}
        
        # Create and run the deletion flow
        deletion_flow = DocumentDeletionFlow()
        await deletion_flow.run_async(shared)
        
        # Verify deletion was successful
        if not shared.get("metadata_deleted") or not shared.get("vectors_deleted"):
            raise HTTPException(
                status_code=500,
                detail="Document deletion workflow failed"
            )
        
        # Log the action for audit purposes
        logger.warning(f"Document {document_id} ({document_check['filename']}) deleted by admin {current_user['user_id']}")
        
        return DocumentDeleteResponse(
            message="Document deleted successfully",
            document_id=document_id,
            deleted_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
    
    finally:
        if database:
            await database.disconnect()


@router.get("/admin/documents/events")
async def document_events_stream(
    token: str = Query(..., description="JWT authentication token")
):
    """
    Server-Sent Events endpoint for real-time document status updates.
    
    Streams document processing status changes to connected clients.
    EventSource doesn't support custom headers, so authentication is done via query parameter.
    
    Returns:
        StreamingResponse with SSE data
    """
    # Verify admin token from query parameter
    try:
        from src.nodes.auth.auth_middleware_node import AuthMiddlewareNode
        
        auth_middleware = AuthMiddlewareNode()
        
        shared_store = {
            "authorization_header": f"Bearer {token}",
            "required_roles": ["admin"]
        }
        
        result = await auth_middleware.run(shared_store)
        
        if not result["authenticated"]:
            # Return 401/403 as SSE response for authentication failures
            async def auth_error_generator():
                yield f"data: {json.dumps({'type': 'error', 'message': result['error']})}\n\n"
            
            return StreamingResponse(
                auth_error_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Methods": "*"
                },
                status_code=result["status_code"]
            )
        
        current_user = {
            "user_id": result["user_id"],
            "email": result["email"],
            "role": result["role"]
        }
        
    except Exception as e:
        logger.error(f"SSE authentication error: {str(e)}")
        async def auth_error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Authentication failed'})}\n\n"
        
        return StreamingResponse(
            auth_error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            },
            status_code=401
        )
    
    async def event_generator():
        logger.info(f"SSE connection established for admin: {current_user['user_id']}")
        
        try:
            while True:
                # Check for document status updates
                # In a real implementation, this would monitor a queue or database for changes
                # For now, we'll send a heartbeat every 30 seconds
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            logger.info(f"SSE connection closed for admin: {current_user['user_id']}")
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )


@router.delete("/admin/users/{user_id}", response_model=UserDeleteResponse)
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> UserDeleteResponse:
    """
    Delete a user (deny and remove from system).
    
    Args:
        user_id: The ID of the user to delete
    
    Returns:
        UserDeleteResponse with deletion confirmation
    """
    database = None
    
    try:
        logger.info(f"User deletion requested by admin: {current_user['user_id']} for user: {user_id}")
        
        # Prevent admin from deleting themselves
        if user_id == current_user["user_id"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete your own admin account"
            )
        
        # Create database connection
        database = Database(settings.database_url)
        await database.connect()
        
        # Check if user exists and get their details for logging
        user_check = await database.fetch_one(
            "SELECT id, email, role FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        
        if not user_check:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Prevent deletion of other admin accounts
        if user_check["role"] == "admin":
            raise HTTPException(
                status_code=403,
                detail="Cannot delete other admin accounts"
            )
        
        # Delete the user
        delete_result = await database.execute(
            "DELETE FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        
        if delete_result == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete user"
            )
        
        # Log the action for audit purposes
        logger.warning(f"User {user_id} ({user_check['email']}) deleted by admin {current_user['user_id']}")
        
        return UserDeleteResponse(
            message="User deleted successfully",
            user_id=user_id,
            deleted_at="2025-01-27T00:00:00Z"  # Would use actual timestamp in production
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )
    
    finally:
        if database:
            await database.disconnect()


# =============================================================================
# SYSTEM CONFIGURATION ENDPOINTS
# =============================================================================

@router.get("/admin/settings", response_model=SystemConfigurationResponse)
async def get_system_settings(
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> SystemConfigurationResponse:
    """
    Get current system configuration settings.
    
    Returns all configurable system settings organized by category.
    """
    database = None
    
    try:
        logger.info(f"System settings requested by admin: {current_user['user_id']}")
        
        # Create database connection
        database = Database(settings.database_url)
        await database.connect()
        
        # Create configuration manager instance
        config_manager = ConfigurationManager(database=database)
        
        # Fetch all configuration settings
        configurations = await config_manager.get_all_configurations()
        
        logger.info(f"System settings retrieved successfully for admin: {current_user['user_id']}")
        return SystemConfigurationResponse(configurations=configurations)
        
    except Exception as e:
        logger.error(f"Failed to retrieve system settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve system settings: {str(e)}"
        )
    
    finally:
        if database:
            await database.disconnect()


@router.patch("/admin/settings")
async def update_system_setting(
    update_request: ConfigurationUpdate,
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    Update a specific system configuration setting.
    """
    database = None
    
    try:
        logger.info(f"Configuration update requested by admin: {current_user['user_id']} "
                   f"for {update_request.category}.{update_request.key}")
        
        # Create database connection
        database = Database(settings.database_url)
        await database.connect()
        
        # Create configuration manager instance
        config_manager = ConfigurationManager(database=database)
        
        # Validate and update the configuration
        updated_config = await config_manager.update_configuration(
            category=update_request.category,
            key=update_request.key,
            value=update_request.value,
            updated_by=current_user['user_id'],
            change_reason=update_request.change_reason
        )
        
        return {
            "message": "Configuration updated successfully",
            "category": update_request.category,
            "key": update_request.key,
            "value": update_request.value,
            "updated_at": updated_config["updated_at"],
            "updated_by": current_user['user_id']
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to update configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
    
    finally:
        if database:
            await database.disconnect()


@router.get("/admin/system/health", response_model=SystemHealth)
async def get_system_health(
    current_user: Dict[str, Any] = Depends(require_admin_role)
) -> SystemHealth:
    """
    Get current system health status.
    """
    try:
        logger.info(f"System health check requested by admin: {current_user['user_id']}")
        
        # Create system health checker instance
        health_checker = SystemHealthChecker()
        
        # Perform comprehensive health check
        health_status = await health_checker.get_system_health()
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to check system health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check system health: {str(e)}")

