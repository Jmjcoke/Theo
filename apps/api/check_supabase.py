#!/usr/bin/env python3
"""
Script to check what's in Supabase vector database
"""

import os
import asyncio
import aiohttp
import json
from src.core.config import get_settings

async def check_supabase():
    """Check what documents are stored in Supabase"""
    
    settings = get_settings()
    print(f"Supabase URL: {settings.supabase_url}")
    
    if not settings.supabase_url or not settings.supabase_service_key:
        print("Supabase configuration not found in settings")
        # Try direct from environment
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        print(f"ENV Supabase URL: {supabase_url}")
        print(f"ENV Supabase Key: {'***' + str(supabase_key)[-4:] if supabase_key else 'None'}")
        
        if not supabase_url:
            print("No Supabase configuration found!")
            return
            
        settings.supabase_url = supabase_url
        settings.supabase_service_key = supabase_key
    
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Try to get document count from documents table
        try:
            url = f"{settings.supabase_url}/rest/v1/documents?select=count"
            async with session.get(url, headers={**headers, "Prefer": "count=exact"}) as response:
                if response.status == 200:
                    count_header = response.headers.get('Content-Range', '')
                    print(f"Documents table count header: {count_header}")
                else:
                    print(f"Documents table request failed: {response.status}")
                    text = await response.text()
                    print(f"Error: {text}")
        except Exception as e:
            print(f"Error checking documents table: {e}")
        
        # Try to get some actual documents with correct columns
        try:
            url = f"{settings.supabase_url}/rest/v1/documents?select=id,content,metadata&limit=5"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Found {len(data)} documents in Supabase:")
                    for doc in data:
                        metadata = doc.get('metadata', {})
                        filename = metadata.get('filename', 'unknown')
                        doc_type = metadata.get('document_type', 'unknown')
                        print(f"  - ID: {doc.get('id')}, Filename: {filename}, Type: {doc_type}, Content length: {len(str(doc.get('content', '')))}")
                else:
                    print(f"Documents query failed: {response.status}")
                    text = await response.text()
                    print(f"Error: {text}")
        except Exception as e:
            print(f"Error querying documents: {e}")
        
        # Try to find documents from specific local DB document IDs
        local_completed_docs = [
            "58067499-5377-4549-b7bf-1981f88ae029_Psalms.json",
            "f543412d-7023-481a-b06f-f1eaeef7b2b4_TestBook.json", 
            "740926f0-a09a-4481-a545-7cc5d1b4aa69_Genesis.json"
        ]
        
        print(f"\nSearching for completed local documents in Supabase:")
        for filename in local_completed_docs:
            try:
                url = f"{settings.supabase_url}/rest/v1/documents?select=id,metadata&metadata->>filename.eq.{filename}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"  - {filename}: {len(data)} matches in Supabase")
                    else:
                        print(f"  - {filename}: Query failed ({response.status})")
            except Exception as e:
                print(f"  - {filename}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(check_supabase())