#!/usr/bin/env python3
"""
Script to check if "processing" documents are actually already in Supabase
and update their status accordingly
"""

import asyncio
import aiohttp
import sqlite3
import json
from src.core.config import get_settings

async def sync_database_status():
    """Check Supabase for local processing documents and update status"""
    
    settings = get_settings()
    
    # Connect to local database
    db_path = "/Users/joshuacoke/dev/Theo/apps/api/theo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all processing documents
    cursor.execute("""
        SELECT id, filename, processing_status 
        FROM documents 
        WHERE processing_status = 'processing'
        ORDER BY created_at ASC
    """)
    
    processing_docs = cursor.fetchall()
    print(f"Found {len(processing_docs)} documents with 'processing' status")
    
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json"
    }
    
    completed_count = 0
    missing_count = 0
    
    async with aiohttp.ClientSession() as session:
        for doc_id, filename, status in processing_docs:
            try:
                # Check if this document exists in Supabase
                url = f"{settings.supabase_url}/rest/v1/documents?select=id&metadata->>filename.eq.{filename}&limit=1"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 0:
                            # Document exists in Supabase, update local status to completed
                            cursor.execute("""
                                UPDATE documents 
                                SET processing_status = 'completed',
                                    updated_at = datetime('now')
                                WHERE id = ?
                            """, (doc_id,))
                            completed_count += 1
                            print(f"✅ Updated {filename} to completed (found in Supabase)")
                        else:
                            missing_count += 1
                            print(f"❌ {filename} not found in Supabase")
                    else:
                        print(f"⚠️  Error checking {filename}: {response.status}")
                        
            except Exception as e:
                print(f"⚠️  Error processing {filename}: {e}")
                
            # Commit every 10 updates
            if (completed_count + missing_count) % 10 == 0:
                conn.commit()
    
    # Final commit
    conn.commit()
    conn.close()
    
    print(f"\n📊 Summary:")
    print(f"  - Updated to completed: {completed_count}")
    print(f"  - Still missing from Supabase: {missing_count}")
    print(f"  - Total processed: {completed_count + missing_count}")

if __name__ == "__main__":
    asyncio.run(sync_database_status())