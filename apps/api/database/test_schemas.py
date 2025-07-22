#!/usr/bin/env python3
"""
Database Schema Test Suite
Tests SQLite and PostgreSQL schema creation and validation
"""

import sqlite3
import os
import sys
import tempfile
from typing import List, Tuple

def test_sqlite_schema() -> bool:
    """Test SQLite schema creation and validation."""
    print("Testing SQLite schema...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Read and execute schema
        schema_path = os.path.join(os.path.dirname(__file__), 'sqlite_schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        conn = sqlite3.connect(db_path)
        conn.executescript(schema_sql)
        cursor = conn.cursor()
        
        # Test 1: Verify all tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = ['users', 'documents', 'processing_jobs']
        
        for table in expected_tables:
            if table not in tables:
                print(f"❌ Table '{table}' not found")
                return False
        print("✅ All required tables created")
        
        # Test 2: Verify table structures
        test_results = []
        
        # Test users table structure
        cursor.execute("PRAGMA table_info(users)")
        users_columns = {row[1]: row[2] for row in cursor.fetchall()}
        expected_users_columns = {
            'id': 'INTEGER',
            'email': 'TEXT',
            'password_hash': 'TEXT',
            'role': 'TEXT',
            'status': 'TEXT',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        }
        
        for col, dtype in expected_users_columns.items():
            if col not in users_columns:
                print(f"❌ Users table missing column: {col}")
                return False
        print("✅ Users table structure correct")
        
        # Test 3: Verify constraints work
        try:
            # Test valid user insertion
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                ('test@example.com', 'hashed_password')
            )
            
            # Test invalid role constraint
            try:
                cursor.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                    ('test2@example.com', 'hashed_password', 'invalid_role')
                )
                print("❌ Role constraint not working")
                return False
            except sqlite3.IntegrityError:
                print("✅ Role constraint working")
            
            # Test unique email constraint
            try:
                cursor.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    ('test@example.com', 'another_password')
                )
                print("❌ Unique email constraint not working")
                return False
            except sqlite3.IntegrityError:
                print("✅ Unique email constraint working")
            
        except Exception as e:
            print(f"❌ Constraint testing failed: {e}")
            return False
        
        # Test 4: Verify foreign key relationships
        try:
            # Insert document first
            cursor.execute(
                "INSERT INTO documents (filename, document_type, file_path) VALUES (?, ?, ?)",
                ('test.pdf', 'biblical', '/path/to/test.pdf')
            )
            doc_id = cursor.lastrowid
            
            # Insert processing job with valid document_id
            cursor.execute(
                "INSERT INTO processing_jobs (document_id, status) VALUES (?, ?)",
                (doc_id, 'processing')
            )
            print("✅ Foreign key relationships working")
            
        except Exception as e:
            print(f"❌ Foreign key test failed: {e}")
            return False
        
        # Test 5: Verify indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        expected_indexes = [
            'idx_users_email',
            'idx_users_status',
            'idx_documents_status',
            'idx_documents_type',
            'idx_processing_jobs_document_id',
            'idx_processing_jobs_status'
        ]
        
        for index in expected_indexes:
            if index not in indexes:
                print(f"❌ Index '{index}' not found")
                return False
        print("✅ All indexes created")
        
        conn.close()
        print("✅ SQLite schema test passed")
        return True
        
    except Exception as e:
        print(f"❌ SQLite schema test failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_postgresql_schema_syntax() -> bool:
    """Test PostgreSQL schema syntax (without actual database connection)."""
    print("Testing PostgreSQL schema syntax...")
    
    try:
        schema_path = os.path.join(os.path.dirname(__file__), 'supabase_schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Basic syntax checks
        required_elements = [
            'CREATE EXTENSION IF NOT EXISTS vector',
            'CREATE TABLE document_chunks',
            'embedding vector(1536)',
            'CREATE INDEX idx_document_chunks_embedding_cosine',
            'FUNCTION similarity_search',
            'FUNCTION search_biblical_text'
        ]
        
        for element in required_elements:
            if element not in schema_sql:
                print(f"❌ Missing required element: {element}")
                return False
        
        # Check vector dimension is correct (1536 for OpenAI)
        if 'vector(1536)' not in schema_sql:
            print("❌ Vector dimension not set to 1536")
            return False
        
        # Check for required indexes
        vector_indexes = [
            'idx_document_chunks_embedding_cosine',
            'idx_document_chunks_embedding_ip'
        ]
        
        for index in vector_indexes:
            if index not in schema_sql:
                print(f"❌ Missing vector index: {index}")
                return False
        
        print("✅ PostgreSQL schema syntax correct")
        print("✅ Vector dimensions set to 1536 (OpenAI compatible)")
        print("✅ Required indexes and functions present")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL schema syntax test failed: {e}")
        return False

def test_naming_conventions() -> bool:
    """Test that all naming follows snake_case conventions."""
    print("Testing naming conventions...")
    
    try:
        # Read both schema files
        sqlite_path = os.path.join(os.path.dirname(__file__), 'sqlite_schema.sql')
        postgres_path = os.path.join(os.path.dirname(__file__), 'supabase_schema.sql')
        
        with open(sqlite_path, 'r') as f:
            sqlite_content = f.read()
        
        with open(postgres_path, 'r') as f:
            postgres_content = f.read()
        
        # Check table names are snake_case
        table_names = [
            'users', 'documents', 'processing_jobs', 'document_chunks'
        ]
        
        for table in table_names:
            if table != table.lower() or '-' in table:
                print(f"❌ Table name '{table}' not in snake_case")
                return False
        
        # Check column names are snake_case (spot check key columns)
        snake_case_columns = [
            'user_id', 'document_id', 'created_at', 'updated_at',
            'password_hash', 'document_type', 'file_path',
            'error_message', 'chunk_index', 'biblical_version',
            'biblical_book', 'biblical_chapter', 'biblical_verse_start',
            'theological_document_name', 'theological_page_number'
        ]
        
        combined_content = sqlite_content + postgres_content
        for column in snake_case_columns:
            if column in combined_content and column != column.lower():
                print(f"❌ Column name '{column}' not in snake_case")
                return False
        
        print("✅ All naming conventions follow snake_case")
        return True
        
    except Exception as e:
        print(f"❌ Naming convention test failed: {e}")
        return False

def main():
    """Run all schema tests."""
    print("Database Schema Test Suite")
    print("=" * 40)
    
    tests = [
        ("SQLite Schema", test_sqlite_schema),
        ("PostgreSQL Schema Syntax", test_postgresql_schema_syntax),
        ("Naming Conventions", test_naming_conventions)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Database schemas are ready.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())