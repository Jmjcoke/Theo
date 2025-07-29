"""
Simple upload test endpoint for debugging
"""
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
from src.middleware.auth_dependencies import require_admin_role
from typing import Dict, Any

router = APIRouter(prefix="/api/admin", tags=["upload-test"])

@router.post("/upload-test")
async def simple_upload_test(
    file: UploadFile = File(...),
    documentType: str = Form(...),
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Simple upload test endpoint to debug issues
    """
    try:
        # Basic file info
        file_content = await file.read()
        file_size = len(file_content)
        
        return {
            "success": True,
            "message": "Upload test successful",
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": file_size,
                "document_type": documentType
            },
            "user_info": {
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "role": current_user["role"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload test failed: {str(e)}"
        )