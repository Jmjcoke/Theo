#!/usr/bin/env python3
"""
Verify Bible books are being processed and stored in Supabase.
"""

import os
import requests
import sqlite3
import time
from dotenv import load_dotenv

load_dotenv()

def check_processing_status():
    """Check processing status of Bible books in SQLite"""
    
    try:
        conn = sqlite3.connect('theo.db')
        cursor = conn.cursor()
        
        # Get Bible books uploaded today
        cursor.execute("""
            SELECT id, original_filename, processing_status, created_at, chunk_count
            FROM documents 
            WHERE original_filename LIKE '%.json' 
            AND original_filename NOT LIKE '%Books.json'
            AND DATE(created_at) = DATE('now')
            ORDER BY id DESC
            LIMIT 70
        """)
        
        bible_books = cursor.fetchall()
        conn.close()
        
        if not bible_books:
            print("❌ No Bible books found uploaded today")
            return {}
        
        status_counts = {}
        processed_books = []
        
        print(f"📚 Found {len(bible_books)} Bible books uploaded today")
        print("=" * 80)
        print(f"{'ID':<4} {'Book Name':<20} {'Status':<12} {'Chunks':<8} {'Created'}")
        print("-" * 80)
        
        for book in bible_books:
            doc_id, filename, status, created_at, chunk_count = book
            book_name = filename.replace('.json', '') if filename else 'Unknown'
            
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status == 'completed':
                processed_books.append(doc_id)
            
            chunk_display = str(chunk_count) if chunk_count else '0'
            created_display = created_at[:16] if created_at else 'Unknown'
            
            print(f"{doc_id:<4} {book_name:<20} {status:<12} {chunk_display:<8} {created_display}")
        
        print("-" * 80)
        print(f"📊 Status Summary:")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        return {
            'total_books': len(bible_books),
            'processed_books': processed_books,
            'status_counts': status_counts
        }
        
    except Exception as e:
        print(f"❌ Error checking processing status: {str(e)}")
        return {}

def check_supabase_storage(processed_books):
    """Check if processed books have chunks in Supabase"""
    
    if not processed_books:
        print("\n⚠️  No processed books to check in Supabase")
        return
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("\n❌ Missing Supabase configuration")
        return
    
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n🔍 Checking Supabase storage for {len(processed_books)} processed books...")
    print("=" * 70)
    
    documents_url = f"{supabase_url}/rest/v1/documents"
    total_chunks = 0
    books_with_chunks = 0
    
    for doc_id in processed_books[:10]:  # Check first 10 to avoid overwhelming output
        try:
            # Query for chunks belonging to this document
            response = requests.get(
                f"{documents_url}?select=id,content&metadata->>document_id=eq.{doc_id}&limit=5",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                chunks = response.json()
                chunk_count = len(chunks)
                
                if chunk_count > 0:
                    books_with_chunks += 1
                    total_chunks += chunk_count
                    
                    # Get a sample of content
                    sample_content = chunks[0].get('content', '')[:100] if chunks else ''
                    print(f"   📖 Document {doc_id}: {chunk_count} chunks (sample: {sample_content}...)")
                else:
                    print(f"   ⚠️  Document {doc_id}: No chunks found")
            else:
                print(f"   ❌ Document {doc_id}: Query failed ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Document {doc_id}: Error - {str(e)}")
    
    print("-" * 70)
    print(f"📈 Supabase Storage Summary:")
    print(f"   Books checked: {min(len(processed_books), 10)}")
    print(f"   Books with chunks: {books_with_chunks}")
    print(f"   Total chunks found: {total_chunks}")
    
    if len(processed_books) > 10:
        print(f"   (Only checked first 10 of {len(processed_books)} processed books)")

def test_search_functionality():
    """Test search functionality with Bible content"""
    
    print(f"\n🔍 Testing search functionality with Bible content...")
    
    edge_function_url = os.getenv('SUPABASE_EDGE_FUNCTION_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not edge_function_url or not supabase_service_key:
        print("❌ Missing search configuration")
        return
    
    headers = {
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    test_queries = [
        "In the beginning God created",
        "love your neighbor",
        "psalm",
        "Matthew",
        "Genesis creation"
    ]
    
    print("=" * 60)
    
    for query in test_queries:
        try:
            payload = {
                'query': query,
                'match_count': 3
            }
            
            response = requests.post(
                edge_function_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"🔍 Query: '{query}'")
                print(f"   Results: {len(results)}")
                
                if results:
                    top_result = results[0]
                    content = top_result.get('content', '')[:80]
                    score = top_result.get('rrf_score', 0)
                    doc_id = top_result.get('metadata', {}).get('document_id', 'Unknown')
                    
                    print(f"   Top result (score {score:.4f}, doc {doc_id}): {content}...")
                print()
                
            else:
                print(f"❌ Search failed for '{query}': {response.status_code}")
                print()
                
        except Exception as e:
            print(f"❌ Error testing search '{query}': {str(e)}")
            print()

def main():
    """Main verification function"""
    
    print("🔍 Bible Books Verification")
    print("=" * 50)
    
    # Step 1: Check processing status
    print("📊 Step 1: Checking processing status...")
    processing_info = check_processing_status()
    
    # Step 2: Check Supabase storage
    if processing_info.get('processed_books'):
        print(f"\n📦 Step 2: Checking Supabase storage...")
        check_supabase_storage(processing_info['processed_books'])
    
    # Step 3: Test search functionality
    print(f"\n🔍 Step 3: Testing search functionality...")
    test_search_functionality()
    
    # Summary
    print(f"\n🎉 Verification Complete!")
    total = processing_info.get('total_books', 0)
    statuses = processing_info.get('status_counts', {})
    completed = statuses.get('completed', 0)
    
    print(f"   📚 Total Bible books uploaded: {total}")
    print(f"   ✅ Successfully processed: {completed}")
    print(f"   📊 Processing status breakdown: {statuses}")
    
    if total > 0:
        completion_rate = (completed / total) * 100
        print(f"   📈 Completion rate: {completion_rate:.1f}%")
        
        if completion_rate < 50:
            print(f"   ⏳ Note: Processing may still be in progress. Check again in a few minutes.")
        elif completion_rate == 100:
            print(f"   🎉 All Bible books have been processed successfully!")

if __name__ == "__main__":
    main()