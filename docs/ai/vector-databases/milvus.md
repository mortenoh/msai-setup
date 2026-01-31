# Milvus

Milvus is an enterprise-scale, cloud-native vector database designed for massive datasets and high-throughput workloads.

## When to Use Milvus

- Billions of vectors
- GPU acceleration required
- Multi-tenancy
- Kubernetes-native deployment
- Real-time streaming ingestion

For smaller workloads, consider [ChromaDB](chroma.md) or [Qdrant](qdrant.md).

## Installation

### Docker Compose (Standalone)

```yaml
# docker-compose.yml
services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    container_name: milvus-etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    image: minio/minio:latest
    container_name: milvus-minio
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio_data:/minio_data
    command: minio server /minio_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  milvus:
    image: milvusdb/milvus:latest
    container_name: milvus-standalone
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - "19530:19530"
      - "9091:9091"
    volumes:
      - milvus_data:/var/lib/milvus
    depends_on:
      - etcd
      - minio

volumes:
  etcd_data:
  minio_data:
  milvus_data:
```

### Python Client

```bash
pip install pymilvus
```

## Basic Usage

### Connect

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# Connect
connections.connect(host="localhost", port="19530")
```

### Create Collection

```python
# Define schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
]

schema = CollectionSchema(fields=fields, description="Document embeddings")

# Create collection
collection = Collection(name="documents", schema=schema)
```

### Create Index

```python
# Index is required for search
index_params = {
    "metric_type": "COSINE",  # or L2, IP
    "index_type": "IVF_FLAT",  # or HNSW, IVF_SQ8, etc.
    "params": {"nlist": 1024}
}

collection.create_index(field_name="embedding", index_params=index_params)
```

### Insert Data

```python
import numpy as np

# Prepare data
embeddings = np.random.rand(1000, 768).tolist()
texts = [f"Document {i}" for i in range(1000)]
sources = ["source.pdf"] * 1000

# Insert
data = [embeddings, texts, sources]
collection.insert(data)

# Flush to persist
collection.flush()
```

### Search

```python
# Load collection into memory
collection.load()

# Search
query_vector = np.random.rand(1, 768).tolist()

results = collection.search(
    data=query_vector,
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=5,
    output_fields=["text", "source"]
)

for hits in results:
    for hit in hits:
        print(f"ID: {hit.id}, Score: {hit.score}")
        print(f"Text: {hit.entity.get('text')[:100]}...")
```

## Index Types

| Index | Best For | Memory | Speed |
|-------|----------|--------|-------|
| FLAT | Small datasets, exact search | High | Slow |
| IVF_FLAT | Balanced recall/speed | Medium | Fast |
| IVF_SQ8 | Memory constrained | Low | Fast |
| HNSW | High recall requirement | High | Very fast |
| GPU_IVF_FLAT | GPU acceleration | GPU | Very fast |

### HNSW Index

```python
index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {
        "M": 16,
        "efConstruction": 200
    }
}
collection.create_index("embedding", index_params)
```

### GPU Index

```python
index_params = {
    "metric_type": "L2",
    "index_type": "GPU_IVF_FLAT",
    "params": {"nlist": 1024}
}
collection.create_index("embedding", index_params)
```

## Filtering

### Scalar Filtering

```python
# Filter by field
results = collection.search(
    data=query_vector,
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=5,
    expr='source == "manual.pdf"',
    output_fields=["text", "source"]
)

# Range filter
results = collection.search(
    data=query_vector,
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=5,
    expr='page >= 10 and page <= 50',
    output_fields=["text", "page"]
)

# IN clause
results = collection.search(
    data=query_vector,
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=5,
    expr='category in ["tech", "science"]',
    output_fields=["text", "category"]
)
```

## Partitions

Organize data for efficient querying:

```python
# Create partition
collection.create_partition("2024_data")

# Insert into partition
collection.insert(data, partition_name="2024_data")

# Search specific partition
results = collection.search(
    data=query_vector,
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=5,
    partition_names=["2024_data"]
)
```

## Collection Management

### List Collections

```python
from pymilvus import utility

collections = utility.list_collections()
print(collections)
```

### Collection Info

```python
print(f"Entities: {collection.num_entities}")
print(f"Partitions: {collection.partitions}")
```

### Drop Collection

```python
collection.drop()
```

## LangChain Integration

```python
from langchain_community.vectorstores import Milvus
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Create from documents
vectorstore = Milvus.from_documents(
    documents,
    embeddings,
    connection_args={"host": "localhost", "port": "19530"},
    collection_name="langchain_docs"
)

# Load existing
vectorstore = Milvus(
    embeddings,
    connection_args={"host": "localhost", "port": "19530"},
    collection_name="langchain_docs"
)

# Search
results = vectorstore.similarity_search("query", k=4)
```

## Performance Tuning

### Memory Management

```python
# Release collection from memory when not in use
collection.release()

# Load when needed
collection.load()

# Load specific partitions only
collection.load(partition_names=["recent_data"])
```

### Batch Operations

```python
# Batch insert
batch_size = 10000
for i in range(0, len(embeddings), batch_size):
    batch_data = [
        embeddings[i:i + batch_size],
        texts[i:i + batch_size],
        sources[i:i + batch_size]
    ]
    collection.insert(batch_data)
collection.flush()
```

### Index Parameters

```python
# Tune search parameters
search_params = {
    "metric_type": "COSINE",
    "params": {
        "nprobe": 16,  # Higher = better recall, slower
        "ef": 64  # For HNSW
    }
}
```

## Monitoring

### Metrics

```bash
# Prometheus metrics
curl http://localhost:9091/metrics
```

### Grafana Dashboard

Milvus provides official Grafana dashboards for monitoring:
- Query performance
- Memory usage
- Index status
- Segment statistics

## Kubernetes Deployment

For production, use Milvus Operator:

```bash
# Install operator
kubectl apply -f https://raw.githubusercontent.com/milvus-io/milvus-operator/main/deploy/manifests/deployment.yaml

# Deploy cluster
kubectl apply -f - <<EOF
apiVersion: milvus.io/v1beta1
kind: Milvus
metadata:
  name: milvus-cluster
spec:
  mode: cluster
  dependencies:
    storage:
      external: false
EOF
```

## See Also

- [Vector Databases Overview](index.md)
- [Qdrant](qdrant.md) - Simpler alternative for production
- [RAG Implementation](../rag/implementation.md)
