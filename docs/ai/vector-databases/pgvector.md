# pgvector

pgvector is a PostgreSQL extension that adds vector similarity search capabilities to your existing PostgreSQL database.

## When to Use pgvector

- Already using PostgreSQL
- Need SQL joins between vectors and relational data
- Want transactional consistency
- Moderate vector workloads (< 10M vectors)
- Don't want to add another database

## Installation

### PostgreSQL Extension

```sql
-- Enable the extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### Docker

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: postgres-vector
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: vectordb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Python Client

```bash
pip install psycopg2-binary pgvector
```

## Basic Usage

### Create Table

```sql
-- Create table with vector column
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    source VARCHAR(255),
    embedding vector(768)  -- 768 dimensions
);
```

### Insert Vectors

```python
import psycopg2
from pgvector.psycopg2 import register_vector

# Connect
conn = psycopg2.connect(
    host="localhost",
    database="vectordb",
    user="postgres",
    password="postgres"
)

# Register vector type
register_vector(conn)

# Insert
cur = conn.cursor()
cur.execute(
    "INSERT INTO documents (content, source, embedding) VALUES (%s, %s, %s)",
    ("Document content", "source.pdf", embedding)  # embedding is a list
)
conn.commit()
```

### Batch Insert

```python
from psycopg2.extras import execute_values

data = [
    (content, source, embedding)
    for content, source, embedding in zip(contents, sources, embeddings)
]

execute_values(
    cur,
    "INSERT INTO documents (content, source, embedding) VALUES %s",
    data
)
conn.commit()
```

### Search

```python
# Cosine similarity (closest = highest score)
cur.execute("""
    SELECT id, content, source, 1 - (embedding <=> %s) as similarity
    FROM documents
    ORDER BY embedding <=> %s
    LIMIT 5
""", (query_embedding, query_embedding))

results = cur.fetchall()
for id, content, source, similarity in results:
    print(f"ID: {id}, Score: {similarity:.4f}")
    print(f"Content: {content[:100]}...")
```

## Distance Functions

| Operator | Function | Description |
|----------|----------|-------------|
| `<->` | L2 distance | Euclidean distance |
| `<#>` | Inner product | Negative inner product |
| `<=>` | Cosine distance | 1 - cosine similarity |

```sql
-- L2 distance (smaller = closer)
SELECT * FROM documents ORDER BY embedding <-> query_vec LIMIT 5;

-- Cosine similarity (convert distance to similarity)
SELECT *, 1 - (embedding <=> query_vec) as similarity
FROM documents
ORDER BY embedding <=> query_vec
LIMIT 5;

-- Inner product (for normalized vectors)
SELECT * FROM documents ORDER BY embedding <#> query_vec LIMIT 5;
```

## Indexing

### IVFFlat Index

Good for most use cases:

```sql
-- Create index
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- For L2 distance
CREATE INDEX ON documents USING ivfflat (embedding vector_l2_ops)
WITH (lists = 100);
```

**Tuning `lists`:**
- Rule of thumb: `lists = sqrt(rows)`
- More lists = faster search, more memory
- Fewer lists = slower search, less memory

### HNSW Index

Better recall, more memory:

```sql
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Parameters:**
- `m`: Max connections per node (16-64)
- `ef_construction`: Build-time search breadth (64-200)

### Search Parameters

```sql
-- Set search parameters for IVFFlat
SET ivfflat.probes = 10;  -- Higher = better recall, slower

-- Set search parameters for HNSW
SET hnsw.ef_search = 100;  -- Higher = better recall, slower
```

## Filtering with Vectors

Combine vector search with SQL filters:

```sql
-- Filter then search
SELECT id, content, 1 - (embedding <=> %s) as similarity
FROM documents
WHERE source = 'manual.pdf'
ORDER BY embedding <=> %s
LIMIT 5;

-- Complex filters
SELECT id, content, 1 - (embedding <=> %s) as similarity
FROM documents
WHERE source IN ('doc1.pdf', 'doc2.pdf')
  AND created_at > '2024-01-01'
ORDER BY embedding <=> %s
LIMIT 5;
```

## Partial Indexes

For filtered queries:

```sql
-- Index only specific sources
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WHERE source = 'manual.pdf';
```

## Hybrid Search

Combine full-text and vector search:

```sql
-- Add full-text search column
ALTER TABLE documents ADD COLUMN tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

CREATE INDEX ON documents USING gin(tsv);

-- Hybrid search with RRF (Reciprocal Rank Fusion)
WITH semantic AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> query_vec) as rank
    FROM documents
    LIMIT 20
),
keyword AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank(tsv, query) DESC) as rank
    FROM documents
    WHERE tsv @@ plainto_tsquery('english', 'search terms')
    LIMIT 20
)
SELECT d.id, d.content,
    COALESCE(1.0 / (60 + s.rank), 0) +
    COALESCE(1.0 / (60 + k.rank), 0) as rrf_score
FROM documents d
LEFT JOIN semantic s ON d.id = s.id
LEFT JOIN keyword k ON d.id = k.id
WHERE s.id IS NOT NULL OR k.id IS NOT NULL
ORDER BY rrf_score DESC
LIMIT 5;
```

## LangChain Integration

```python
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")

CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/vectordb"

# Create from documents
vectorstore = PGVector.from_documents(
    documents,
    embeddings,
    connection_string=CONNECTION_STRING,
    collection_name="langchain_docs"
)

# Load existing
vectorstore = PGVector(
    embeddings=embeddings,
    connection_string=CONNECTION_STRING,
    collection_name="langchain_docs"
)

# Search
results = vectorstore.similarity_search("query", k=4)

# Search with filter
results = vectorstore.similarity_search(
    "query",
    k=4,
    filter={"source": "manual.pdf"}
)
```

## SQLAlchemy Integration

```python
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, Session
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    source = Column(String(255))
    embedding = Column(Vector(768))

# Create engine
engine = create_engine('postgresql://postgres:postgres@localhost:5432/vectordb')
Base.metadata.create_all(engine)

# Insert
with Session(engine) as session:
    doc = Document(
        content="Document content",
        source="source.pdf",
        embedding=embedding_list
    )
    session.add(doc)
    session.commit()

# Search
with Session(engine) as session:
    results = session.query(Document).order_by(
        Document.embedding.cosine_distance(query_embedding)
    ).limit(5).all()
```

## Performance Tips

### Maintenance

```sql
-- Analyze after bulk inserts
ANALYZE documents;

-- Vacuum to reclaim space
VACUUM documents;
```

### Connection Pooling

```python
from psycopg2 import pool

connection_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    host="localhost",
    database="vectordb",
    user="postgres",
    password="postgres"
)

conn = connection_pool.getconn()
# ... use connection ...
connection_pool.putconn(conn)
```

### Index Build Time

```sql
-- Increase maintenance_work_mem for faster index builds
SET maintenance_work_mem = '2GB';
CREATE INDEX ...;
```

## Limitations

- Single-node only (PostgreSQL clustering needed for HA)
- No GPU acceleration
- Performance degrades beyond ~10M vectors
- Index must fit in memory for best performance

## See Also

- [Vector Databases Overview](index.md)
- [ChromaDB](chroma.md) - Dedicated vector database
- [RAG Implementation](../rag/implementation.md)
