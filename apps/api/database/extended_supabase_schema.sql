-- Extended Supabase Schema
-- This adds document metadata tracking to the existing schema

-- Step 1: Ensure vector extension exists
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Documents table (should already exist)
-- This table stores the actual chunks with embeddings
CREATE TABLE IF NOT EXISTS documents (
  id bigint primary key generated always as identity,
  content text,
  fts tsvector generated always as (to_tsvector('english', content)) stored,
  embedding vector(1536),
  metadata jsonb
);

-- Step 3: Create document_metadata table
-- This table bridges SQLite metadata with Supabase content
CREATE TABLE IF NOT EXISTS document_metadata (
  id bigint primary key generated always as identity,
  
  -- Bridge to SQLite
  sqlite_document_id text unique not null,
  
  -- Document information
  original_filename text,
  filename text,
  document_type text check (document_type in ('biblical', 'theological', 'other')),
  
  -- File details
  file_size bigint,
  mime_type text,
  file_path text,
  
  -- Processing status
  processing_status text default 'queued' check (processing_status in ('queued', 'processing', 'completed', 'failed')),
  
  -- Upload details
  uploaded_by text,
  uploaded_at timestamptz default now(),
  
  -- Processing details
  processed_at timestamptz,
  chunk_count integer default 0,
  stored_chunk_count integer default 0,
  
  -- Timestamps
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  
  -- Additional metadata (JSON)
  extra_metadata jsonb default '{}'::jsonb
);

-- Step 4: Create indexes for document_metadata
CREATE INDEX IF NOT EXISTS idx_document_metadata_sqlite_id ON document_metadata(sqlite_document_id);
CREATE INDEX IF NOT EXISTS idx_document_metadata_filename ON document_metadata(original_filename);
CREATE INDEX IF NOT EXISTS idx_document_metadata_type ON document_metadata(document_type);
CREATE INDEX IF NOT EXISTS idx_document_metadata_status ON document_metadata(processing_status);
CREATE INDEX IF NOT EXISTS idx_document_metadata_uploaded_at ON document_metadata(uploaded_at);

-- Step 5: Create indexes for documents table (if not already exist)
CREATE INDEX IF NOT EXISTS documents_fts_idx ON documents USING gin(fts);
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents USING hnsw (embedding vector_ip_ops);
CREATE INDEX IF NOT EXISTS documents_metadata_document_id_idx ON documents USING gin ((metadata->>'document_id'));

-- Step 6: Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Step 7: Create trigger for updated_at
DROP TRIGGER IF EXISTS update_document_metadata_updated_at ON document_metadata;
CREATE TRIGGER update_document_metadata_updated_at
    BEFORE UPDATE ON document_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Step 8: Create function to get document summary
CREATE OR REPLACE FUNCTION get_document_summary(doc_id text)
RETURNS TABLE (
  sqlite_id text,
  filename text,
  document_type text,
  chunk_count bigint,
  processing_status text,
  uploaded_at timestamptz
)
LANGUAGE sql
AS $$
  SELECT 
    dm.sqlite_document_id,
    dm.original_filename,
    dm.document_type,
    count(d.id) as chunk_count,
    dm.processing_status,
    dm.uploaded_at
  FROM document_metadata dm
  LEFT JOIN documents d ON (d.metadata->>'document_id') = dm.sqlite_document_id
  WHERE dm.sqlite_document_id = doc_id
  GROUP BY dm.sqlite_document_id, dm.original_filename, dm.document_type, dm.processing_status, dm.uploaded_at;
$$;

-- Step 9: Create function to sync document counts
CREATE OR REPLACE FUNCTION sync_document_chunk_counts()
RETURNS void
LANGUAGE sql
AS $$
  UPDATE document_metadata 
  SET stored_chunk_count = subquery.chunk_count,
      updated_at = now()
  FROM (
    SELECT 
      (d.metadata->>'document_id') as doc_id,
      count(*) as chunk_count
    FROM documents d
    WHERE d.metadata->>'document_id' IS NOT NULL
    GROUP BY (d.metadata->>'document_id')
  ) AS subquery
  WHERE document_metadata.sqlite_document_id = subquery.doc_id;
$$;

-- Step 10: Keep existing hybrid search function
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text text,
  query_embedding vector(1536),
  match_count int,
  full_text_weight float = 1,
  semantic_weight float = 1,
  rrf_k int = 50
)
RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  rrf_score float
)
LANGUAGE sql
AS $$
WITH full_text AS (
  SELECT
    id,
    row_number() over(order by ts_rank_cd(fts, websearch_to_tsquery(query_text)) desc) as rank_ix
  FROM
    documents
  WHERE
    fts @@ websearch_to_tsquery(query_text)
  LIMIT least(match_count, 30) * 2
),
semantic AS (
  SELECT
    id,
    row_number() over (order by embedding <#> query_embedding) as rank_ix
  FROM
    documents
  LIMIT least(match_count, 30) * 2
)
SELECT
  d.id,
  d.content,
  d.metadata,
  coalesce(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
    coalesce(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight as rrf_score
FROM
  full_text
  FULL OUTER JOIN semantic
    ON full_text.id = semantic.id
  JOIN documents d
    ON coalesce(full_text.id, semantic.id) = d.id
ORDER BY
  rrf_score desc
LIMIT
  least(match_count, 30)
$$;

-- Step 11: Create a view for document overview
CREATE OR REPLACE VIEW document_overview AS
SELECT 
  dm.sqlite_document_id,
  dm.original_filename,
  dm.document_type,
  dm.processing_status,
  dm.uploaded_at,
  dm.chunk_count as expected_chunks,
  dm.stored_chunk_count as actual_chunks,
  CASE 
    WHEN dm.stored_chunk_count > 0 THEN 'synced'
    WHEN dm.processing_status = 'completed' AND dm.stored_chunk_count = 0 THEN 'missing_chunks'
    ELSE 'pending'
  END as sync_status
FROM document_metadata dm
ORDER BY dm.uploaded_at DESC;

-- Initial sync of existing documents (run this after applying schema)
-- INSERT INTO document_metadata (sqlite_document_id, original_filename, document_type, processing_status, chunk_count)
-- SELECT DISTINCT
--   (metadata->>'document_id')::text,
--   'Unknown', -- You'll need to populate this from SQLite
--   'unknown', -- You'll need to populate this from SQLite  
--   'completed',
--   count(*) OVER (PARTITION BY metadata->>'document_id')
-- FROM documents 
-- WHERE metadata->>'document_id' IS NOT NULL
-- ON CONFLICT (sqlite_document_id) DO NOTHING;