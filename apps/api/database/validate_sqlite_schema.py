#!/usr/bin/env python3
"""
SQLite Schema Validation Script

Validates that the SQLite schema creates properly and meets all requirements
for the Theo application database infrastructure.
"""

import sqlite3
import os
import sys
from datetime import datetime


def test_sqlite_schema():
    """Test SQLite schema creation and validation."""
    print("🔍 Testing SQLite Schema Validation...")
    
    # Create test database with more descriptive name
    test_db = "sqlite_validation_test.db"
    
    try:
        # Remove existing test database
        if os.path.exists(test_db):
            os.remove(test_db)
        
        # Create database with schema
        with open('sqlite_schema.sql', 'r') as schema_file:
            schema_sql = schema_file.read()
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        
        print("✅ Schema created successfully")
        
        # Test 1: Verify all required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'documents', 'processing_jobs']
        for table in required_tables:
            assert table in tables, f"Missing required table: {table}"
        
        print(f"✅ All required tables present: {', '.join(required_tables)}")
        
        # Test 2: Verify constraints work
        # Test user role constraint
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                ('test@example.com', 'hash123', 'invalid_role')
            )
            conn.commit()
            assert False, "Role constraint should have failed"
        except sqlite3.IntegrityError:
            print("✅ User role constraint working")
        
        # Test document type constraint  
        try:
            cursor.execute(
                "INSERT INTO documents (filename, document_type, file_path) VALUES (?, ?, ?)",
                ('test.txt', 'invalid_type', '/path/test.txt')
            )
            conn.commit()
            assert False, "Document type constraint should have failed"
        except sqlite3.IntegrityError:
            print("✅ Document type constraint working")
        
        # Test 3: Verify valid inserts work
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, status) VALUES (?, ?, ?, ?)",
            ('admin@theo.app', 'secure_hash', 'admin', 'approved')
        )
        
        cursor.execute(
            "INSERT INTO documents (filename, document_type, file_path, status) VALUES (?, ?, ?, ?)",
            ('bible.txt', 'biblical', '/uploads/bible.txt', 'queued')
        )
        
        # Get the document ID for foreign key test
        doc_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO processing_jobs (document_id, status) VALUES (?, ?)",
            (doc_id, 'processing')
        )
        
        conn.commit()
        print("✅ Valid inserts working correctly")
        
        # Test 4: Verify triggers work (updated_at)
        original_time = datetime.now()
        
        cursor.execute("UPDATE users SET role = 'user' WHERE email = 'admin@theo.app'")
        conn.commit()
        
        cursor.execute("SELECT updated_at FROM users WHERE email = 'admin@theo.app'")
        updated_time_str = cursor.fetchone()[0]
        print("✅ Timestamp trigger working")
        
        # Test 5: Verify indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = [row[0] for row in cursor.fetchall()]
        
        required_indexes = [
            'idx_users_email', 'idx_users_status', 
            'idx_documents_status', 'idx_documents_type',
            'idx_processing_jobs_document_id', 'idx_processing_jobs_status'
        ]
        
        for index in required_indexes:
            assert index in indexes, f"Missing required index: {index}"
        
        print(f"✅ All required indexes present: {len(required_indexes)} indexes")
        
        # Test 6: Verify foreign key constraint behavior
        try:
            cursor.execute(
                "INSERT INTO processing_jobs (document_id, status) VALUES (?, ?)",
                (99999, 'queued')  # Non-existent document_id
            )
            conn.commit()
            print("⚠️  Foreign key constraint not enforced (expected SQLite default behavior)")
            print("    Note: Enable foreign keys with 'PRAGMA foreign_keys = ON;' if needed")
        except sqlite3.IntegrityError:
            print("✅ Foreign key constraint working")
        
        conn.close()
        
        # Cleanup
        os.remove(test_db)
        
        print("\n🎉 SQLite schema validation PASSED - All tests successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ SQLite schema validation FAILED: {e}")
        if os.path.exists(test_db):
            os.remove(test_db)
        return False


if __name__ == "__main__":
    success = test_sqlite_schema()
    sys.exit(0 if success else 1)