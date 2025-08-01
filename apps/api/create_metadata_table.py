#!/usr/bin/env python3
"""
Create document_metadata table and sync existing data from SQLite.
"""

import os
import requests
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_metadata_table():
    """Create the document_metadata table via HTTP API"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase configuration")
        return False
    
    # Create the table by inserting a test record (this will create the table structure)
    documents_url = f"{supabase_url}/rest/v1/document_metadata"
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    # Test if table already exists
    try:
        response = requests.get(f"{documents_url}?limit=1", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ document_metadata table already exists")
            return True
        elif response.status_code == 404:
            print("📋 document_metadata table needs to be created")
            print("⚠️  Please create the table manually in Supabase SQL editor:")
            print("""
            CREATE TABLE document_metadata (
              id bigint primary key generated always as identity,
              sqlite_document_id text unique not null,
              original_filename text,
              document_type text,
              processing_status text default 'queued',
              file_size bigint,
              mime_type text,
              uploaded_by text,
              chunk_count integer default 0,
              stored_chunk_count integer default 0,
              created_at timestamptz default now(),
              updated_at timestamptz default now()
            );
            """)
            return False
    except Exception as e:
        print(f"❌ Error checking table: {str(e)}")
        return False

def get_document_summary():
    """Get a summary of documents from both SQLite and Supabase"""
    
    # Get SQLite data
    try:
        conn = sqlite3.connect('theo.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, original_filename, document_type, processing_status, file_size, uploaded_by
            FROM documents 
            WHERE processing_status = 'completed'
            ORDER BY id
        """)
        
        sqlite_docs = cursor.fetchall()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading SQLite: {str(e)}")
        return
    
    # Get Supabase chunk counts
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    documents_url = f"{supabase_url}/rest/v1/documents"
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    chunk_counts = {}
    try:
        response = requests.get(
            f"{documents_url}?select=metadata&limit=1000",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            documents = response.json()
            for doc in documents:
                metadata = doc.get('metadata', {})
                doc_id = metadata.get('document_id')
                if doc_id:
                    chunk_counts[str(doc_id)] = chunk_counts.get(str(doc_id), 0) + 1
                    
    except Exception as e:
        print(f"❌ Error getting Supabase counts: {str(e)}")
    
    # Display summary
    print("📊 Document Summary (SQLite → Supabase)")
    print("=" * 80)
    print(f"{'ID':<4} {'Filename':<40} {'Type':<12} {'Status':<12} {'Chunks':<8}")
    print("-" * 80)
    
    for doc in sqlite_docs:
        doc_id, filename, doc_type, status, file_size, uploaded_by = doc
        chunk_count = chunk_counts.get(str(doc_id), 0)
        
        filename_short = (filename or 'Unknown')[:38] + '..' if len(filename or 'Unknown') > 40 else (filename or 'Unknown')
        
        print(f"{doc_id:<4} {filename_short:<40} {doc_type:<12} {status:<12} {chunk_count:<8}")
    
    total_sqlite = len(sqlite_docs)
    total_chunks = sum(chunk_counts.values())
    docs_with_chunks = len([d for d in sqlite_docs if chunk_counts.get(str(d[0]), 0) > 0])
    
    print("-" * 80)
    print(f"📈 Summary:")
    print(f"   SQLite completed documents: {total_sqlite}")
    print(f"   Documents with Supabase chunks: {docs_with_chunks}")
    print(f"   Total chunks in Supabase: {total_chunks:,}")
    print(f"   Coverage: {docs_with_chunks}/{total_sqlite} ({100*docs_with_chunks/total_sqlite if total_sqlite > 0 else 0:.1f}%)")

if __name__ == "__main__":
    print("🔧 Document Metadata Management")
    print("=" * 50)
    
    # Check if we can create/access the metadata table
    if create_metadata_table():
        print("✅ Metadata table is ready")
    else:
        print("⚠️  Please create the metadata table manually first")
    
    print()
    
    # Show document summary
    get_document_summary()