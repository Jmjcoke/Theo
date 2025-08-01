"""
Minimal FastAPI Application for Authentication Testing

This is a stripped-down version to test the authentication fix
without import issues from other modules.
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
    title="Theo API - Authentication Test",
    description="Minimal API for testing authentication fixes",
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

# Include auth and admin routers for testing
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "theo-auth-test"}

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {"message": "Theo Authentication Test API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)