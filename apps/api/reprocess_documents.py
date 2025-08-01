#!/usr/bin/env python3
"""
Script to reprocess stuck and failed documents
"""

import asyncio
import logging
import sqlite3
from src.core.celery_app import celery_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Reprocess documents that are stuck or failed"""
    
    # Connect to database
    db_path = "/Users/joshuacoke/dev/Theo/apps/api/theo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all documents that need reprocessing
    cursor.execute("""
        SELECT id, filename, processing_status 
        FROM documents 
        WHERE processing_status IN ('processing', 'failed', 'queued')
        ORDER BY created_at ASC
        LIMIT 10
    """)
    
    documents = cursor.fetchall()
    logger.info(f"Found {len(documents)} documents to reprocess")
    
    # Reset documents to queued status
    document_ids = [str(doc[0]) for doc in documents]
    if document_ids:
        placeholders = ','.join(['?' for _ in document_ids])
        cursor.execute(f"""
            UPDATE documents 
            SET processing_status = 'queued', 
                updated_at = datetime('now'),
                error_message = NULL
            WHERE id IN ({placeholders})
        """, document_ids)
        conn.commit()
        logger.info(f"Reset {len(document_ids)} documents to queued status")
    
    # Submit processing tasks to Celery
    for doc_id, filename, status in documents:
        logger.info(f"Submitting document {doc_id} ({filename}) for processing")
        
        # Submit to Celery queue
        task = celery_app.send_task(
            'process_document',
            args=[str(doc_id)],
            queue='default'
        )
        
        logger.info(f"Task {task.id} submitted for document {doc_id}")
    
    conn.close()
    logger.info("Reprocessing tasks submitted successfully")

if __name__ == "__main__":
    asyncio.run(main())