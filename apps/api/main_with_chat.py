"""
FastAPI Backend Application for Theo with Chat Support

Modified version that includes chat functionality while avoiding missing modules.
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
from src.api.admin import router as admin_router
from src.api.chat import router as chat_router
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
    title="Theo API with Chat",
    description="AI-powered theological research API with chat functionality",
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

# Include API routers
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])


@app.get("/health", response_model=Dict[str, str], tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify server is running correctly.
    """
    return {"status": "ok"}


@app.get("/api/health", response_model=Dict[str, str], tags=["Health"])
async def api_health_check() -> Dict[str, str]:
    """
    API health check endpoint to verify API server is running correctly.
    """
    return {"status": "ok", "service": "api"}


@app.get("/api/admin/dashboard", response_model=Dict[str, str], tags=["Admin"])
async def admin_dashboard_status() -> Dict[str, str]:
    """
    Basic admin dashboard status endpoint - temporary fix for frontend compatibility.
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
    """
    return JSONResponse(
        content={
            "message": "Welcome to Theo API with Chat",
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