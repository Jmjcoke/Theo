# Background Processing Architecture

## Celery/Redis Integration

**Task Queue Architecture**:
```python
from celery import Celery

celery_app = Celery(
    "theo_workers",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def process_document_async(document_id: str):
    """Background document processing task"""
    # Initialize AsyncFlow for background processing
    flow = DocumentProcessingFlow()
    result = asyncio.run(flow.run({"document_id": document_id}))
    return result
```

**Progress Tracking via SSE**:
```python
@app.get("/api/progress/{task_id}")
async def stream_progress(task_id: str):
    """Server-Sent Events for progress updates"""
    
    async def event_stream():
        while not task_complete(task_id):
            progress = get_task_progress(task_id)
            yield f"data: {json.dumps(progress)}\n\n"
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_stream())
```
