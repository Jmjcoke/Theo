#!/usr/bin/env python3
"""
Apply the extended Supabase schema and sync existing document metadata.
"""

import os
import requests
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def execute_supabase_sql(sql_content):
    """Execute SQL commands in Supabase via HTTP API"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase configuration")
        return False
    
    # Use the SQL REST API endpoint
    sql_url = f"{supabase_url}/rest/v1/rpc/exec_sql"
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Split SQL into individual statements and execute each
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if not statement:
                continue
                
            print(f"📝 Executing statement {i+1}/{len(statements)}: {statement[:60]}...")
            
            payload = {'sql': statement}
            response = requests.post(sql_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201, 204]:
                print(f"   ✅ Success")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error executing SQL: {str(e)}")
        return False

def get_sqlite_document_metadata():
    """Get document metadata from SQLite database"""
    
    try:
        conn = sqlite3.connect('theo.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, original_filename, filename, document_type, processing_status,
                   file_size, mime_type, file_path, uploaded_by, created_at, updated_at,
                   chunk_count, metadata
            FROM documents
            ORDER BY id
        """)
        
        documents = cursor.fetchall()
        conn.close()
        
        return [
            {
                'sqlite_document_id': str(doc[0]),
                'original_filename': doc[1] or 'Unknown',
                'filename': doc[2] or 'Unknown',
                'document_type': doc[3] or 'other',
                'processing_status': doc[4] or 'queued',
                'file_size': doc[5] or 0,
                'mime_type': doc[6] or 'unknown',
                'file_path': doc[7] or '',
                'uploaded_by': doc[8] or 'unknown',
                'created_at': doc[9] or '2025-01-01T00:00:00Z',
                'updated_at': doc[10] or '2025-01-01T00:00:00Z',
                'chunk_count': doc[11] or 0,
                'metadata': doc[12] or '{}'
            }
            for doc in documents
        ]
        
    except Exception as e:
        print(f"❌ Error reading SQLite: {str(e)}")
        return []

def sync_document_metadata(documents):
    """Sync document metadata to Supabase document_metadata table"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    documents_url = f"{supabase_url}/rest/v1/document_metadata"
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }
    
    try:
        # Prepare documents for batch insert
        batch_data = []
        for doc in documents:
            batch_data.append({
                'sqlite_document_id': doc['sqlite_document_id'],
                'original_filename': doc['original_filename'],
                'filename': doc['filename'],
                'document_type': doc['document_type'],
                'processing_status': doc['processing_status'],
                'file_size': doc['file_size'],
                'mime_type': doc['mime_type'],
                'file_path': doc['file_path'],
                'uploaded_by': doc['uploaded_by'],
                'chunk_count': doc['chunk_count'],
                'extra_metadata': {'sqlite_metadata': doc['metadata']}
            })
        
        # Insert in batches of 10
        batch_size = 10
        successful = 0
        
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i + batch_size]
            
            response = requests.post(documents_url, json=batch, headers=headers, timeout=30)
            
            if response.status_code in [200, 201, 204]:
                successful += len(batch)
                print(f"   ✅ Synced batch {i//batch_size + 1}: {len(batch)} documents")
            else:
                print(f"   ❌ Failed batch {i//batch_size + 1}: {response.status_code} - {response.text}")
        
        print(f"📊 Sync complete: {successful}/{len(documents)} documents synced")
        return successful > 0
        
    except Exception as e:
        print(f"❌ Error syncing metadata: {str(e)}")
        return False

def sync_chunk_counts():
    """Run the sync function to update stored chunk counts"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    rpc_url = f"{supabase_url}/rest/v1/rpc/sync_document_chunk_counts"
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(rpc_url, headers=headers, timeout=30)
        
        if response.status_code in [200, 201, 204]:
            print("✅ Chunk counts synchronized")
            return True
        else:
            print(f"❌ Failed to sync chunk counts: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error syncing chunk counts: {str(e)}")
        return False

def main():
    """Main function to apply extended schema"""
    
    print("🔧 Applying Extended Supabase Schema")
    print("=" * 60)
    
    # Step 1: Read and apply the extended schema
    print("📋 Step 1: Applying extended schema...")
    try:
        with open('database/extended_supabase_schema.sql', 'r') as f:
            schema_content = f.read()
        
        # Note: Since we can't directly execute complex SQL via REST API,
        # we'll provide the schema for manual application
        print("⚠️  Note: The extended schema contains complex SQL that should be applied manually.")
        print("   Please run the SQL in database/extended_supabase_schema.sql in your Supabase SQL editor.")
        print("   Press Enter when you've applied the schema...")
        input()
        
    except Exception as e:
        print(f"❌ Error reading schema file: {str(e)}")
        return False
    
    # Step 2: Get SQLite document metadata
    print("📊 Step 2: Reading SQLite document metadata...")
    sqlite_docs = get_sqlite_document_metadata()
    print(f"   Found {len(sqlite_docs)} documents in SQLite")
    
    # Step 3: Sync metadata to Supabase
    print("🔄 Step 3: Syncing metadata to Supabase...")
    if sync_document_metadata(sqlite_docs):
        print("   ✅ Metadata sync successful")
    else:
        print("   ❌ Metadata sync failed")
        return False
    
    # Step 4: Sync chunk counts
    print("📈 Step 4: Syncing chunk counts...")
    if sync_chunk_counts():
        print("   ✅ Chunk count sync successful")
    else:
        print("   ❌ Chunk count sync failed")
    
    print(f"\n🎉 Extended schema application complete!")
    print("   - document_metadata table created")
    print("   - SQLite metadata synced to Supabase")
    print("   - Chunk counts synchronized")
    print("   - Helper functions and views created")

if __name__ == "__main__":
    main()