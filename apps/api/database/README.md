# Database Setup Guide

This directory contains the database schemas and setup instructions for the Theo application. The application uses a dual-database architecture:

- **SQLite**: Local development database for metadata storage
- **Supabase (PostgreSQL + pgvector)**: Production vector database for embeddings

## Files in this Directory

- `sqlite_schema.sql` - SQLite database schema for local development
- `supabase_schema.sql` - PostgreSQL schema for Supabase with vector support
- `README.md` - This setup guide
- `local.db` - SQLite database file (created after initialization)

## SQLite Database Setup

### Prerequisites
- SQLite 3.x installed on your system
- Python with sqlite3 module (included in standard library)

### Initialization Process

1. **Navigate to the database directory:**
   ```bash
   cd apps/api/database
   ```

2. **Create the SQLite database:**
   ```bash
   sqlite3 local.db < sqlite_schema.sql
   ```

3. **Verify the tables were created:**
   ```bash
   sqlite3 local.db ".tables"
   # Expected output: documents processing_jobs users
   ```

4. **Check the schema:**
   ```bash
   sqlite3 local.db ".schema"
   ```

### SQLite Database Schema

The SQLite database contains the following tables:

#### `users` Table
- **Purpose**: User authentication and authorization
- **Fields**: id, email, password_hash, role, status, created_at, updated_at
- **Constraints**: 
  - Unique email addresses
  - Role must be 'user' or 'admin'
  - Status must be 'pending', 'approved', or 'denied'

#### `documents` Table
- **Purpose**: File metadata tracking
- **Fields**: id, filename, document_type, file_path, status, created_at, updated_at
- **Constraints**:
  - Document type must be 'biblical', 'theological', or 'other'
  - Status must be 'queued', 'processing', 'completed', or 'failed'

#### `processing_jobs` Table
- **Purpose**: Background job tracking for document processing
- **Fields**: id, document_id, status, error_message, created_at, updated_at
- **Relationships**: Foreign key to documents table

### Environment Variables for SQLite

Add these environment variables to your `.env` file:

```env
# SQLite Database Configuration
SQLITE_DATABASE_PATH=apps/api/database/local.db
SQLITE_DATABASE_URL=sqlite:///apps/api/database/local.db
```

## Supabase Database Setup

### Prerequisites
- Supabase project created at [supabase.com](https://supabase.com)
- Project API key and URL
- Database password for direct SQL access

### Initialization Process

1. **Enable pgvector extension** (if not already enabled):
   - Go to your Supabase dashboard
   - Navigate to Database → Extensions
   - Enable the `vector` extension

2. **Run the schema script**:
   - Go to SQL Editor in Supabase dashboard
   - Copy and paste the contents of `supabase_schema.sql`
   - Execute the script

3. **Verify the setup**:
   ```sql
   -- Check if pgvector extension is enabled
   SELECT * FROM pg_extension WHERE extname = 'vector';
   
   -- Check if tables were created
   \dt
   
   -- Verify vector column type
   \d document_chunks
   ```

### Supabase Database Schema

#### `document_chunks` Table
- **Purpose**: Store text chunks with vector embeddings for semantic search
- **Key Fields**:
  - `content`: The actual text content
  - `embedding`: 1536-dimensional vector from OpenAI embeddings
  - `biblical_*`: Metadata for biblical text references
  - `theological_*`: Metadata for theological document references

#### Vector Search Functions

The schema includes helper functions for semantic search:

- `similarity_search()`: General semantic search across all chunks
- `search_biblical_text()`: Search specifically within biblical texts with version filtering

### Environment Variables for Supabase

Add these environment variables to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

**Note**: Replace placeholders with your actual Supabase project details.

## Connection Examples

### SQLite Connection (Python)

```python
import sqlite3
import os

def get_sqlite_connection():
    db_path = os.getenv('SQLITE_DATABASE_PATH', 'apps/api/database/local.db')
    return sqlite3.connect(db_path)

# Usage
conn = get_sqlite_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
conn.close()
```

### Supabase Connection (Python)

```python
import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    return create_client(url, key)

# Usage
supabase = get_supabase_client()
result = supabase.table('document_chunks').select('*').limit(10).execute()
```

## Data Migration and Maintenance

### Backup Procedures

**SQLite Backup:**
```bash
sqlite3 local.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"
```

**Supabase Backup:**
- Use Supabase dashboard backup features
- Or use pg_dump with connection details

### Common Maintenance Tasks

**View table sizes:**
```sql
-- SQLite
SELECT name, COUNT(*) as row_count 
FROM sqlite_master 
JOIN pragma_table_info(sqlite_master.name) 
GROUP BY name;

-- PostgreSQL (Supabase)
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE tablename IN ('document_chunks');
```

**Monitor vector index performance:**
```sql
-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats 
WHERE tablename = 'document_chunks' AND attname = 'embedding';
```

## Troubleshooting

### Common Issues

1. **SQLite Permission Errors**:
   - Ensure the database directory is writable
   - Check file permissions: `chmod 664 local.db`

2. **Supabase Connection Timeouts**:
   - Verify environment variables are set correctly
   - Check network connectivity to Supabase
   - Ensure API keys have correct permissions

3. **Vector Search Performance**:
   - Monitor index usage with `EXPLAIN ANALYZE`
   - Consider adjusting `lists` parameter in vector indexes
   - Ensure sufficient memory for vector operations

4. **Schema Validation Errors**:
   - Check constraint violations in error messages
   - Verify data types match schema definitions
   - Ensure foreign key relationships are maintained

### Getting Help

- SQLite Documentation: [https://sqlite.org/docs.html](https://sqlite.org/docs.html)
- Supabase Documentation: [https://supabase.com/docs](https://supabase.com/docs)
- pgvector Documentation: [https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)