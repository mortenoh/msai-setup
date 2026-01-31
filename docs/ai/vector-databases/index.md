# Vector Databases

Vector databases store and search high-dimensional embeddings, enabling semantic search and RAG applications.

## Why Vector Databases?

Traditional databases search by exact matches. Vector databases search by meaning:

```
Query: "How do I fix authentication errors?"

Traditional DB: Searches for exact keywords
Vector DB: Finds documents about login issues, auth failures, credential problems
```

## How They Work

```
┌─────────────────────────────────────────────────────────────┐
│                    Vector Database                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Text → Embedding Model → Vector [0.23, -0.45, ..., 0.89] │
│                              │                              │
│                              v                              │
│                     ┌───────────────┐                       │
│                     │  Index (HNSW) │                       │
│                     └───────────────┘                       │
│                              │                              │
│   Query → Embedding → Nearest Neighbor Search → Results    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Database Comparison

| Feature | ChromaDB | Qdrant | Milvus | pgvector |
|---------|----------|--------|--------|----------|
| **Ease of use** | Excellent | Good | Moderate | Good |
| **Performance** | Good | Excellent | Excellent | Moderate |
| **Scalability** | Single node | Distributed | Distributed | PostgreSQL limits |
| **Filtering** | Basic | Advanced | Advanced | SQL |
| **Persistence** | File/Memory | File/Server | Server | PostgreSQL |
| **GPU support** | No | No | Yes | No |
| **Best for** | Development | Production | Enterprise | PostgreSQL users |

## In This Section

| Document | Description |
|----------|-------------|
| [ChromaDB](chroma.md) | Simple, local-first vector database |
| [Qdrant](qdrant.md) | High-performance production database |
| [Milvus](milvus.md) | Enterprise-scale vector database |
| [pgvector](pgvector.md) | PostgreSQL extension for vectors |

## Quick Start

### ChromaDB (Simplest)

```python
import chromadb
from chromadb.utils import embedding_functions

# Create client
client = chromadb.PersistentClient(path="./chroma_db")

# Use Ollama embeddings
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings"
)

# Create collection
collection = client.get_or_create_collection(
    name="documents",
    embedding_function=ollama_ef
)

# Add documents
collection.add(
    documents=["Machine learning is...", "Deep learning uses..."],
    ids=["doc1", "doc2"],
    metadatas=[{"source": "ml.pdf"}, {"source": "dl.pdf"}]
)

# Search
results = collection.query(
    query_texts=["What is neural network?"],
    n_results=2
)
```

### Qdrant (Production)

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

# Add vectors
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=1,
            vector=embedding_model.embed("Machine learning is..."),
            payload={"source": "ml.pdf", "page": 1}
        )
    ]
)

# Search
results = client.search(
    collection_name="documents",
    query_vector=embedding_model.embed("What is ML?"),
    limit=5
)
```

## Choosing a Database

### Use ChromaDB when:
- Prototyping and development
- Single-user applications
- Small to medium datasets (< 1M vectors)
- You want the simplest setup

### Use Qdrant when:
- Production deployments
- Need advanced filtering
- Distributed/replicated setup
- High query throughput

### Use Milvus when:
- Enterprise scale (billions of vectors)
- GPU acceleration needed
- Multi-tenancy required
- Kubernetes-native deployment

### Use pgvector when:
- Already using PostgreSQL
- Need SQL joins with vector search
- Transactional consistency required
- Moderate vector workloads

## Embedding Models

All databases work with these local embedding models:

| Model | Dimensions | Speed | Quality |
|-------|------------|-------|---------|
| nomic-embed-text | 768 | Fast | Good |
| mxbai-embed-large | 1024 | Medium | Better |
| all-minilm | 384 | Very fast | Basic |
| bge-m3 | 1024 | Medium | Best multilingual |

```bash
# Pull models with Ollama
ollama pull nomic-embed-text
ollama pull mxbai-embed-large
```

## See Also

- [RAG Implementation](../rag/index.md)
- [Embeddings Guide](../models/embeddings.md)
- [Ollama Integration](../inference-engines/ollama/index.md)
