#!/usr/bin/env python3
"""
Supabase Schema Validation Script

Validates that the Supabase schema includes all required components
for vector embeddings and PocketFlow integration.
"""

import re
import sys


def validate_supabase_schema_file():
    """Validate Supabase schema file contains all required components."""
    print("🔍 Testing Supabase Schema File Validation...")
    
    try:
        schema_path = 'supabase_schema.sql'
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # Test 1: Verify pgvector extension
        assert 'CREATE EXTENSION IF NOT EXISTS vector' in schema_content, \
            "Missing pgvector extension creation"
        print("✅ pgvector extension creation found")
        
        # Test 2: Verify document_chunks table
        assert 'CREATE TABLE document_chunks' in schema_content, \
            "Missing document_chunks table"
        print("✅ document_chunks table definition found")
        
        # Test 3: Verify 1536-dimensional vector column (OpenAI standard)
        assert 'embedding vector(1536)' in schema_content, \
            "Missing 1536-dimensional embedding column"
        print("✅ 1536-dimensional vector column found (OpenAI compatible)")
        
        # Test 4: Verify biblical metadata columns
        biblical_fields = [
            'biblical_version', 'biblical_book', 'biblical_chapter',
            'biblical_verse_start', 'biblical_verse_end'
        ]
        for field in biblical_fields:
            assert field in schema_content, f"Missing biblical field: {field}"
        print("✅ All biblical metadata fields present")
        
        # Test 5: Verify theological metadata columns
        theological_fields = [
            'theological_document_name', 'theological_page_number', 'theological_section'
        ]
        for field in theological_fields:
            assert field in schema_content, f"Missing theological field: {field}"
        print("✅ All theological metadata fields present")
        
        # Test 6: Verify vector indexes
        vector_indexes = [
            'idx_document_chunks_embedding_cosine',
            'idx_document_chunks_embedding_ip'
        ]
        for index in vector_indexes:
            assert index in schema_content, f"Missing vector index: {index}"
        print("✅ Vector search indexes present (cosine and inner product)")
        
        # Test 7: Verify search functions
        search_functions = ['similarity_search', 'search_biblical_text']
        for func in search_functions:
            assert f'CREATE OR REPLACE FUNCTION {func}' in schema_content, \
                f"Missing search function: {func}"
        print("✅ Vector search functions present")
        
        # Test 8: Verify Row Level Security
        assert 'ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY' in schema_content, \
            "Missing RLS configuration"
        assert 'CREATE POLICY' in schema_content, \
            "Missing RLS policies"
        print("✅ Row Level Security configured")
        
        # Test 9: Verify timestamp functions and triggers
        assert 'update_updated_at_column()' in schema_content, \
            "Missing timestamp update function"
        assert 'CREATE TRIGGER update_document_chunks_updated_at' in schema_content, \
            "Missing timestamp trigger"
        print("✅ Automatic timestamp updates configured")
        
        # Test 10: Verify PocketFlow compatibility (1536 dimensions)
        # Count occurrences of 1536 to ensure consistency
        dimension_count = schema_content.count('1536')
        assert dimension_count >= 3, \
            f"Expected at least 3 references to 1536 dimensions, found {dimension_count}"
        print(f"✅ PocketFlow dimension consistency: {dimension_count} references to 1536-dim vectors")
        
        # Test 11: Verify performance indexes for metadata
        metadata_indexes = [
            'idx_document_chunks_document_id',
            'idx_document_chunks_biblical_book',
            'idx_document_chunks_biblical_version',
            'idx_document_chunks_theological_document'
        ]
        for index in metadata_indexes:
            assert index in schema_content, f"Missing metadata index: {index}"
        print("✅ Metadata performance indexes present")
        
        # Test 12: Check for vector operation examples
        vector_ops = ['<=>']  # Cosine distance operator
        for op in vector_ops:
            assert op in schema_content, f"Missing vector operation: {op}"
        print("✅ Vector distance operations configured")
        
        print("\n🎉 Supabase schema validation PASSED - All requirements met!")
        print("📋 Summary:")
        print("   • pgvector extension enabled")
        print("   • 1536-dimensional vectors (OpenAI compatible)")  
        print("   • Biblical and theological metadata support")
        print("   • Vector similarity search functions")
        print("   • Performance-optimized indexes")
        print("   • Row Level Security configured")
        print("   • PocketFlow chunking/embedding patterns supported")
        
        return True
        
    except FileNotFoundError:
        print("❌ supabase_schema.sql file not found")
        return False
    except Exception as e:
        print(f"\n❌ Supabase schema validation FAILED: {e}")
        return False


def validate_pocketflow_compatibility():
    """Verify schema supports PocketFlow patterns from documentation."""
    print("\n🔍 Validating PocketFlow Compatibility...")
    
    try:
        schema_path = 'supabase_schema.sql'
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # PocketFlow chunking support
        chunking_requirements = [
            'chunk_index',      # Chunk ordering
            'content',          # Text content storage  
            'document_id',      # Source document linking
        ]
        
        for req in chunking_requirements:
            assert req in schema_content, f"Missing PocketFlow chunking requirement: {req}"
        
        print("✅ PocketFlow chunking patterns supported")
        
        # PocketFlow embedding support (OpenAI recommended)
        embedding_requirements = [
            'vector(1536)',     # OpenAI text-embedding-ada-002
            'similarity_search', # Vector search function
            'vector_cosine_ops', # Cosine similarity
        ]
        
        for req in embedding_requirements:
            assert req in schema_content, f"Missing PocketFlow embedding requirement: {req}"
        
        print("✅ PocketFlow embedding patterns supported")
        print("✅ OpenAI text-embedding-ada-002 compatibility confirmed")
        
        return True
        
    except Exception as e:
        print(f"❌ PocketFlow compatibility check failed: {e}")
        return False


if __name__ == "__main__":
    schema_valid = validate_supabase_schema_file()
    pocketflow_valid = validate_pocketflow_compatibility()
    
    success = schema_valid and pocketflow_valid
    sys.exit(0 if success else 1)