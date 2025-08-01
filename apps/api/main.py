"""
FastAPI Backend Application for Theo

This is the main entry point for the Theo backend API.
Provides a basic FastAPI application with health check endpoint.
"""

import os
from dotenv import load_dotenv
from typing import Dict

# Load environment variables from .env file
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from src.api.auth_routes import router as auth_router
from src.api.protected_routes import router as protected_router
from src.api.queue_routes import router as queue_router
from src.api.document_routes import router as document_router
from src.api.sse_routes import router as sse_router
from src.api.admin import router as admin_router
from src.api.chat import router as chat_router
from src.api.export import router as export_router
from src.api.simple_upload_test import router as upload_test_router
from src.api.simple_document_upload import router as simple_upload_router
from src.api.editor_routes import router as editor_router
from src.utils.database_utils import init_database
from src.core.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown"""
    # Startup
    await init_database()
    await redis_client.connect()
    yield
    # Shutdown - cleanup if needed
    await redis_client.disconnect()

# Create FastAPI application instance
app = FastAPI(
    title="Theo API",
    description="AI-powered document management and chat platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers in priority order
# Enhanced upload router first to take precedence over legacy routes
app.include_router(simple_upload_router, tags=["Enhanced Document Upload"])
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(protected_router, prefix="/api", tags=["Protected"])
app.include_router(queue_router, prefix="/api", tags=["Queue Management"])
app.include_router(document_router, tags=["Document Upload (Legacy)"])
app.include_router(sse_router, tags=["Server-Sent Events"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(export_router, prefix="/api", tags=["Export"])
app.include_router(editor_router, tags=["Document Editor"])
app.include_router(upload_test_router, tags=["Upload Test"])


@app.get("/health", response_model=Dict[str, str], tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify server is running correctly.
    
    Returns:
        dict: Status response indicating server health
        
    Example:
        ```json
        {"status": "ok"}
        ```
    """
    return {"status": "ok"}


@app.get("/api/health", response_model=Dict[str, str], tags=["Health"])
async def api_health_check() -> Dict[str, str]:
    """
    API health check endpoint to verify API server is running correctly.
    
    Returns:
        dict: Status response indicating API health
    """
    return {"status": "ok", "service": "api"}


@app.get("/api/admin/dashboard", response_model=Dict[str, str], tags=["Admin"])
async def admin_dashboard_status() -> Dict[str, str]:
    """
    Basic admin dashboard status endpoint - temporary fix for frontend compatibility.
    
    Returns:
        dict: Basic status indicating admin API is accessible
    """
    return {
        "status": "ok", 
        "service": "admin", 
        "message": "Admin dashboard API is running. Use /api/admin/dashboard/metrics for full metrics."
    }


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Root endpoint providing basic API information.
    
    Returns:
        JSONResponse: API welcome message with documentation links
    """
    return JSONResponse(
        content={
            "message": "Welcome to Theo API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )