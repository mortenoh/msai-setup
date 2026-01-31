# Qdrant

Qdrant is a high-performance vector database designed for production workloads with advanced filtering capabilities.

## Installation

### Docker (Recommended)

```yaml
# docker-compose.yml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"  # REST API
      - "6334:6334"  # gRPC
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334

volumes:
  qdrant_data:
```

```bash
docker compose up -d
```

### Python Client

```bash
pip install qdrant-client
```

## Basic Usage

### Connect

```python
from qdrant_client import QdrantClient

# Local Docker
client = QdrantClient(host="localhost", port=6333)

# In-memory (development)
client = QdrantClient(":memory:")

# Persistent local storage
client = QdrantClient(path="./qdrant_data")
```

### Create Collection

```python
from qdrant_client.models import VectorParams, Distance

client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=768,  # Embedding dimension
        distance=Distance.COSINE  # or EUCLID, DOT
    )
)
```

### Insert Vectors

```python
from qdrant_client.models import PointStruct

# Single point
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, ...],  # 768 dimensions
            payload={"source": "doc.pdf", "page": 1, "text": "..."}
        )
    ]
)

# Batch insert
points = [
    PointStruct(id=i, vector=vectors[i], payload=payloads[i])
    for i in range(len(vectors))
]
client.upsert(collection_name="documents", points=points)
```

### Search

```python
results = client.search(
    collection_name="documents",
    query_vector=[0.1, 0.2, ...],
    limit=5
)

for result in results:
    print(f"ID: {result.id}, Score: {result.score}")
    print(f"Payload: {result.payload}")
```

## Advanced Features

### Filtering

Qdrant has powerful filtering capabilities:

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# Exact match
results = client.search(
    collection_name="documents",
    query_vector=query_vec,
    query_filter=Filter(
        must=[
            FieldCondition(key="source", match=MatchValue(value="manual.pdf"))
        ]
    ),
    limit=5
)

# Range filter
results = client.search(
    collection_name="documents",
    query_vector=query_vec,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="page",
                range=Range(gte=10, lte=50)
            )
        ]
    ),
    limit=5
)

# Multiple conditions
results = client.search(
    collection_name="documents",
    query_vector=query_vec,
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="tech")),
            FieldCondition(key="year", range=Range(gte=2023))
        ],
        must_not=[
            FieldCondition(key="status", match=MatchValue(value="draft"))
        ]
    ),
    limit=5
)

# Match any in list
from qdrant_client.models import MatchAny

results = client.search(
    collection_name="documents",
    query_vector=query_vec,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchAny(any=["tech", "science", "ai"])
            )
        ]
    ),
    limit=5
)
```

### Named Vectors

Store multiple vector types per point:

```python
from qdrant_client.models import VectorParams, Distance

# Create collection with multiple vector types
client.create_collection(
    collection_name="multi_vector",
    vectors_config={
        "content": VectorParams(size=768, distance=Distance.COSINE),
        "summary": VectorParams(size=384, distance=Distance.COSINE),
    }
)

# Insert with multiple vectors
client.upsert(
    collection_name="multi_vector",
    points=[
        PointStruct(
            id=1,
            vector={
                "content": content_embedding,
                "summary": summary_embedding
            },
            payload={"text": "..."}
        )
    ]
)

# Search specific vector
results = client.search(
    collection_name="multi_vector",
    query_vector=("content", query_vec),
    limit=5
)
```

### Sparse Vectors (Hybrid Search)

```python
from qdrant_client.models import SparseVectorParams, SparseIndexParams

# Create with both dense and sparse
client.create_collection(
    collection_name="hybrid",
    vectors_config={"dense": VectorParams(size=768, distance=Distance.COSINE)},
    sparse_vectors_config={
        "sparse": SparseVectorParams(index=SparseIndexParams())
    }
)

# Insert
from qdrant_client.models import SparseVector

client.upsert(
    collection_name="hybrid",
    points=[
        PointStruct(
            id=1,
            vector={
                "dense": dense_embedding,
                "sparse": SparseVector(
                    indices=[1, 42, 1337],
                    values=[0.5, 0.8, 0.2]
                )
            }
        )
    ]
)
```

### Quantization

Reduce memory usage with quantization:

```python
from qdrant_client.models import (
    VectorParams, Distance,
    ScalarQuantization, ScalarQuantizationConfig, ScalarType
)

# Scalar quantization (int8)
client.create_collection(
    collection_name="quantized",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type=ScalarType.INT8,
            quantile=0.99,
            always_ram=True
        )
    )
)
```

### Payload Indexing

Speed up filtering with indexes:

```python
client.create_payload_index(
    collection_name="documents",
    field_name="category",
    field_schema="keyword"  # keyword, integer, float, bool, geo, datetime
)
```

## Collection Management

### Get Collection Info

```python
info = client.get_collection(collection_name="documents")
print(f"Vectors: {info.vectors_count}")
print(f"Points: {info.points_count}")
print(f"Status: {info.status}")
```

### Update Collection

```python
from qdrant_client.models import OptimizersConfigDiff

client.update_collection(
    collection_name="documents",
    optimizer_config=OptimizersConfigDiff(
        indexing_threshold=10000
    )
)
```

### Delete Collection

```python
client.delete_collection(collection_name="old_collection")
```

### Snapshots

```python
# Create snapshot
client.create_snapshot(collection_name="documents")

# List snapshots
snapshots = client.list_snapshots(collection_name="documents")

# Recover from snapshot
client.recover_snapshot(
    collection_name="documents",
    location="file:///path/to/snapshot.snapshot"
)
```

## LangChain Integration

```python
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Create from documents
vectorstore = Qdrant.from_documents(
    documents,
    embeddings,
    url="http://localhost:6333",
    collection_name="langchain_docs"
)

# Load existing
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
vectorstore = Qdrant(
    client=client,
    collection_name="langchain_docs",
    embeddings=embeddings
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

## Production Configuration

### Docker Compose with Resources

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
      - ./config.yaml:/qdrant/config/production.yaml
    environment:
      - QDRANT__LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 4G

volumes:
  qdrant_data:
```

### Configuration File

```yaml
# config.yaml
storage:
  storage_path: /qdrant/storage
  snapshots_path: /qdrant/snapshots
  on_disk_payload: true  # Save memory

service:
  max_request_size_mb: 32
  grpc_port: 6334

optimizers:
  default_segment_number: 4
  indexing_threshold: 20000
```

### Clustering

```yaml
services:
  qdrant-1:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__CLUSTER__P2P__PORT=6335
    # ...

  qdrant-2:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__CLUSTER__P2P__PORT=6335
      - QDRANT__CLUSTER__BOOTSTRAP=http://qdrant-1:6335
    # ...
```

## Performance Tips

### Batch Operations

```python
# Use batches for large inserts
batch_size = 1000
for i in range(0, len(points), batch_size):
    batch = points[i:i + batch_size]
    client.upsert(collection_name="documents", points=batch)
```

### Async Client

```python
from qdrant_client import AsyncQdrantClient
import asyncio

async def async_search():
    client = AsyncQdrantClient(host="localhost", port=6333)

    results = await client.search(
        collection_name="documents",
        query_vector=query_vec,
        limit=5
    )
    return results

asyncio.run(async_search())
```

### Parallel Queries

```python
import asyncio

async def parallel_search(queries):
    client = AsyncQdrantClient(host="localhost", port=6333)

    tasks = [
        client.search(
            collection_name="documents",
            query_vector=q,
            limit=5
        )
        for q in queries
    ]

    return await asyncio.gather(*tasks)
```

## Monitoring

### Metrics Endpoint

```bash
curl http://localhost:6333/metrics
```

### Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
```

## See Also

- [Vector Databases Overview](index.md)
- [ChromaDB](chroma.md) - Simpler alternative
- [RAG Implementation](../rag/implementation.md)
