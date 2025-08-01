#!/usr/bin/env python3
"""
Upload all Bible books via the API.
"""

import os
import requests
import json
import time
from pathlib import Path

def upload_bible_books():
    """Upload all Bible books from the directory"""
    
    # API configuration
    API_BASE_URL = "http://localhost:8001"
    bible_books_dir = "/Users/joshuacoke/dev/Theo/Books of the bible"
    
    # Login first to get auth token
    login_data = {
        "email": "admin@theo.ai",
        "password": "admin123"
    }
    
    print("🔐 Logging in to get auth token...")
    try:
        login_response = requests.post(
            f"{API_BASE_URL}/api/login",
            json=login_data,
            timeout=10
        )
        
        if login_response.status_code == 200:
            auth_data = login_response.json()
            auth_token = auth_data.get('access_token')
            print(f"✅ Login successful, got token: {auth_token[:20]}...")
        else:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return
    
    # Get list of Bible book files
    bible_books_path = Path(bible_books_dir)
    json_files = list(bible_books_path.glob("*.json"))
    
    # Filter out Books.json and keep only the actual Bible books
    bible_books = [f for f in json_files if f.name != "Books.json"]
    bible_books.sort()  # Sort alphabetically
    
    print(f"📚 Found {len(bible_books)} Bible books to upload")
    print("=" * 70)
    
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    
    uploaded_count = 0
    failed_count = 0
    
    for i, book_path in enumerate(bible_books, 1):
        book_name = book_path.stem  # Get filename without extension
        
        print(f"📖 [{i:2d}/{len(bible_books)}] Uploading {book_name}...")
        
        try:
            # Read the JSON content
            with open(book_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Prepare the upload
            files = {
                'file': (f"{book_name}.json", content, 'application/json')
            }
            
            data = {
                'documentType': 'biblical',
                'category': 'Bible'
            }
            
            # Upload the file
            upload_response = requests.post(
                f"{API_BASE_URL}/api/admin/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if upload_response.status_code in [200, 201]:
                result = upload_response.json()
                document_id = result.get('document_id')
                filename = result.get('filename', book_name)
                
                print(f"   ✅ Upload successful!")
                print(f"   📄 Document ID: {document_id}")
                print(f"   📝 Filename: {filename}")
                
                uploaded_count += 1
                
                # Brief pause between uploads
                time.sleep(1)
                
            else:
                print(f"   ❌ Upload failed: {upload_response.status_code}")
                print(f"   📝 Response: {upload_response.text}")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ Upload error: {str(e)}")
            failed_count += 1
        
        print()
    
    print("=" * 70)
    print(f"📊 Upload Summary:")
    print(f"   ✅ Successful uploads: {uploaded_count}")
    print(f"   ❌ Failed uploads: {failed_count}")
    print(f"   📖 Total Bible books: {len(bible_books)}")
    
    if uploaded_count > 0:
        print(f"\n⏳ Note: Files are now queued for processing.")
        print(f"   Processing will happen automatically in the background.")
        print(f"   You can monitor progress in the admin interface.")

if __name__ == "__main__":
    print("📚 Bible Books Upload Script")
    print("=" * 50)
    upload_bible_books()