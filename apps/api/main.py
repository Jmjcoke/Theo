"""
FastAPI Backend Application for Theo

This is the main entry point for the Theo backend API.
Provides a basic FastAPI application with health check endpoint.
"""

from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create FastAPI application instance
app = FastAPI(
    title="Theo API",
    description="AI-powered document management and chat platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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