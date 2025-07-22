-- Supabase PostgreSQL Database Schema
-- Vector database for embeddings and document chunks
-- Created: 2025-07-22
-- Version: 1.0

-- Enable pgvector extension for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Document chunks table for storing text content with vector embeddings
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-ada-002 produces 1536-dimensional vectors
    
    -- Biblical citation metadata
    biblical_version TEXT, -- e.g., 'ESV', 'NIV', 'KJV'
    biblical_book TEXT,    -- e.g., 'Genesis', 'Matthew'
    biblical_chapter INTEGER,
    biblical_verse_start INTEGER,
    biblical_verse_end INTEGER,
    
    -- Theological citation metadata
    theological_document_name TEXT,
    theological_page_number INTEGER,
    theological_section TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure chunk index is unique per document
    UNIQUE(document_id, chunk_index)
);

-- Indexes for performance optimization
-- Vector similarity search index (uses cosine distance)
CREATE INDEX idx_document_chunks_embedding_cosine ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Vector similarity search index (uses inner product)
CREATE INDEX idx_document_chunks_embedding_ip ON document_chunks 
    USING ivfflat (embedding vector_ip_ops) 
    WITH (lists = 100);

-- Regular indexes for metadata queries
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_biblical_book ON document_chunks(biblical_book);
CREATE INDEX idx_document_chunks_biblical_version ON document_chunks(biblical_version);
CREATE INDEX idx_document_chunks_theological_document ON document_chunks(theological_document_name);
CREATE INDEX idx_document_chunks_created_at ON document_chunks(created_at);

-- Composite indexes for common query patterns
CREATE INDEX idx_document_chunks_biblical_reference ON document_chunks(biblical_version, biblical_book, biblical_chapter);
CREATE INDEX idx_document_chunks_theological_reference ON document_chunks(theological_document_name, theological_page_number);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at timestamps
CREATE TRIGGER update_document_chunks_updated_at
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
-- Note: These will need to be customized based on authentication implementation
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Example policy (to be refined during authentication implementation)
CREATE POLICY "Users can view their own document chunks" ON document_chunks
    FOR SELECT USING (true); -- Temporarily allow all reads for development

CREATE POLICY "Users can insert their own document chunks" ON document_chunks
    FOR INSERT WITH CHECK (true); -- Temporarily allow all inserts for development

-- Helpful functions for vector operations
CREATE OR REPLACE FUNCTION similarity_search(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.78,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    document_id bigint,
    content text,
    similarity float
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        id,
        document_id,
        content,
        1 - (embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Function for biblical text search with version support
CREATE OR REPLACE FUNCTION search_biblical_text(
    query_embedding vector(1536),
    bible_version text DEFAULT NULL,
    match_threshold float DEFAULT 0.78,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    content text,
    biblical_version text,
    biblical_book text,
    biblical_chapter integer,
    biblical_verse_start integer,
    biblical_verse_end integer,
    similarity float
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        id,
        content,
        biblical_version,
        biblical_book,
        biblical_chapter,
        biblical_verse_start,
        biblical_verse_end,
        1 - (embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE 
        biblical_version IS NOT NULL
        AND (bible_version IS NULL OR biblical_version = bible_version)
        AND 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;