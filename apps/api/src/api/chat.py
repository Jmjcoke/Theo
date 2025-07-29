"""
Chat API Routes for Theo RAG System

FastAPI router for chat interactions with RAG pipeline integration.
Implements protected chat endpoint with JWT authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import uuid
import time
import logging

from src.models.chat_models import ChatRequest, ChatResponse, DocumentSource
from src.middleware.auth_dependencies import require_user_role
from src.flows.chat_flow import ChatFlow
import os

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and chat flow
router = APIRouter()
chat_flow = ChatFlow()

# Feature flag for advanced RAG pipeline
ADVANCED_RAG_ENABLED = os.getenv("ADVANCED_RAG_ENABLED", "true").lower() == "true"


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(require_user_role)
) -> ChatResponse:
    """
    Protected chat endpoint for RAG-based question answering
    
    Requires user or admin authentication. Processes user queries through
    either BasicRAGFlow or AdvancedRAGFlow (with re-ranking and hermeneutics)
    based on feature flag configuration.
    """
    start_time = time.time()
    
    try:
        # Generate unique message ID
        message_id = str(uuid.uuid4())
        
        # Determine which pipeline to use for RAG queries
        use_advanced_pipeline = ADVANCED_RAG_ENABLED and request.useAdvancedPipeline != False
        
        # Prepare shared store for chat flow with intent recognition
        shared_store = {
            "message": request.message,  # For intent recognition
            "context": request.context,
            "session_id": request.sessionId,
            "message_id": message_id,
            "user_id": current_user["user_id"],
            "user_role": current_user["role"],
            "useAdvancedPipeline": use_advanced_pipeline
        }
        
        # Execute chat flow with intent recognition
        result = await chat_flow.run(shared_store)
        
        # Handle flow execution errors
        if not result.get("success", False):
            logger.error(f"Chat flow failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process chat request: {result.get('error', 'Unknown error')}"
            )
        
        # Get processing time from chat metadata or calculate fallback
        chat_metadata = result.get("chat_metadata", {})
        processing_time = chat_metadata.get("processing_time_ms", int((time.time() - start_time) * 1000))
        
        # Format document sources
        sources = []
        for source_data in result.get("sources", []):
            sources.append(DocumentSource(
                documentId=source_data["document_id"],
                title=source_data["title"],
                excerpt=source_data["excerpt"],
                relevance=source_data["relevance"],
                citation=source_data.get("citation")
            ))
        
        # Create base response with intent information
        response_data = {
            "response": result["response"],
            "confidence": result["confidence"],
            "sources": sources,
            "processingTime": processing_time,
            "sessionId": request.sessionId,
            "messageId": message_id,
            "intent": result.get("intent", "new_query"),
            "intentConfidence": result.get("intent_confidence", 0.0)
        }
        
        # Add advanced pipeline metadata if available (only for RAG queries)
        intent = result.get("intent", "new_query")
        if intent == "new_query" and "chat_metadata" in result:
            rag_metadata = chat_metadata.get("rag_metadata", {})
            if rag_metadata and use_advanced_pipeline:
                response_data.update({
                    "advancedPipeline": {
                        "reranking_applied": rag_metadata.get("reranking_applied", False),
                        "hermeneutics_applied": rag_metadata.get("hermeneutics_applied", False),
                        "hermeneutics_version": rag_metadata.get("hermeneutics_metadata", {}).get("version", ""),
                        "pipeline_stages": {
                            "total_latency": rag_metadata.get("total_pipeline_time", 0)
                        }
                    }
                })
        
        # Return chat response
        return ChatResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing chat request"
        )