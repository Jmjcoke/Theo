#!/usr/bin/env python3
"""
Script to check if remaining queued/failed documents are already in Supabase
"""

import asyncio
import aiohttp
import sqlite3
import json
from src.core.config import get_settings

async def check_remaining_documents():
    """Check if queued/failed documents are already in Supabase"""
    
    settings = get_settings()
    
    # Connect to local database
    db_path = "/Users/joshuacoke/dev/Theo/apps/api/theo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all queued and failed documents
    cursor.execute("""
        SELECT id, filename, processing_status 
        FROM documents 
        WHERE processing_status IN ('queued', 'failed')
        ORDER BY processing_status, created_at
    """)
    
    remaining_docs = cursor.fetchall()
    print(f"Checking {len(remaining_docs)} queued/failed documents...")
    
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json"
    }
    
    already_processed = 0
    truly_missing = 0
    error_count = 0
    
    async with aiohttp.ClientSession() as session:
        for doc_id, filename, status in remaining_docs:
            try:
                # Check if this document exists in Supabase
                url = f"{settings.supabase_url}/rest/v1/documents?select=id&metadata->>filename.eq.{filename}&limit=1"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 0:
                            # Document exists in Supabase
                            already_processed += 1
                            print(f"✅ {status} -> completed: {filename} (found in Supabase)")
                            
                            # Update local status to completed
                            cursor.execute("""
                                UPDATE documents 
                                SET processing_status = 'completed',
                                    updated_at = datetime('now')
                                WHERE id = ?
                            """, (doc_id,))
                        else:
                            truly_missing += 1
                            print(f"❌ {status}: {filename} (not in Supabase)")
                    else:
                        error_count += 1
                        print(f"⚠️  Error checking {filename}: HTTP {response.status}")
                        
            except Exception as e:
                error_count += 1
                print(f"⚠️  Error processing {filename}: {e}")
                
            # Commit every 10 updates
            if (already_processed + truly_missing + error_count) % 10 == 0:
                conn.commit()
    
    # Final commit
    conn.commit()
    
    # Get final status counts
    cursor.execute('SELECT processing_status, COUNT(*) FROM documents GROUP BY processing_status ORDER BY COUNT(*) DESC')
    final_counts = cursor.fetchall()
    
    conn.close()
    
    print(f"\n📊 Results:")
    print(f"  - Documents already in Supabase (updated to completed): {already_processed}")
    print(f"  - Documents truly missing from Supabase: {truly_missing}")
    print(f"  - Errors during check: {error_count}")
    
    print(f"\n📊 Final database status:")
    for status, count in final_counts:
        print(f"  - {status}: {count}")

if __name__ == "__main__":
    asyncio.run(check_remaining_documents())