-- Database Schema
-- Apply this to Supabase SQL Editor

-- Step 1: Create vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Create documents table
CREATE TABLE documents (
  id bigint primary key generated always as identity,
  content text,
  fts tsvector generated always as (to_tsvector('english', content)) stored,
  embedding vector(1536),
  metadata jsonb
);

-- Step 3: Create full-text search index
CREATE INDEX ON documents USING gin(fts);

-- Step 4: Create vector search index
CREATE INDEX ON documents USING hnsw (embedding vector_ip_ops);

-- Step 5: Drop existing function and create hybrid search function
DROP FUNCTION IF EXISTS hybrid_search;

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