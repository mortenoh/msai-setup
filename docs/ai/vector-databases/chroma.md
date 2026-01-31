# ChromaDB

ChromaDB is an open-source, local-first vector database designed for simplicity and ease of use.

## Installation

```bash
pip install chromadb
```

## Basic Usage

### In-Memory (Development)

```python
import chromadb

# Ephemeral client (data lost on restart)
client = chromadb.Client()

# Create collection
collection = client.create_collection(name="my_collection")

# Add documents
collection.add(
    documents=["Document 1 content", "Document 2 content"],
    ids=["id1", "id2"]
)

# Query
results = collection.query(
    query_texts=["search query"],
    n_results=2
)
```

### Persistent Storage

```python
import chromadb
from chromadb.config import Settings

# Persistent client
client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

# Get or create collection
collection = client.get_or_create_collection(name="documents")
```

### Client-Server Mode

```bash
# Start server
chroma run --host localhost --port 8000 --path ./chroma_db
```

```python
import chromadb

# Connect to server
client = chromadb.HttpClient(host="localhost", port=8000)
```

## Embedding Functions

### Default (Sentence Transformers)

```python
# Uses all-MiniLM-L6-v2 by default
collection = client.create_collection(name="default_embeddings")
```

### Ollama Embeddings

```python
from chromadb.utils import embedding_functions

ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings"
)

collection = client.create_collection(
    name="ollama_collection",
    embedding_function=ollama_ef
)
```

### Custom Embedding Function

```python
from chromadb import Documents, EmbeddingFunction, Embeddings
import requests

class CustomEmbedding(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        # Call your embedding API
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": input[0]}
        )
        return [response.json()["embedding"]]

collection = client.create_collection(
    name="custom",
    embedding_function=CustomEmbedding()
)
```

## Document Operations

### Adding Documents

```python
# With auto-generated embeddings
collection.add(
    documents=["Doc 1", "Doc 2", "Doc 3"],
    ids=["1", "2", "3"],
    metadatas=[
        {"source": "file1.pdf", "page": 1},
        {"source": "file2.pdf", "page": 1},
        {"source": "file2.pdf", "page": 2}
    ]
)

# With pre-computed embeddings
collection.add(
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
    documents=["Doc 1", "Doc 2"],
    ids=["1", "2"]
)
```

### Updating Documents

```python
collection.update(
    ids=["1"],
    documents=["Updated content"],
    metadatas=[{"source": "file1.pdf", "page": 1, "updated": True}]
)
```

### Upserting Documents

```python
# Insert or update
collection.upsert(
    ids=["1", "4"],
    documents=["Updated doc 1", "New doc 4"]
)
```

### Deleting Documents

```python
# By ID
collection.delete(ids=["1", "2"])

# By filter
collection.delete(where={"source": "file1.pdf"})
```

## Querying

### Basic Query

```python
results = collection.query(
    query_texts=["What is machine learning?"],
    n_results=5
)

# Results structure
print(results["ids"])        # [["id1", "id2", ...]]
print(results["documents"])  # [["doc1", "doc2", ...]]
print(results["distances"])  # [[0.1, 0.2, ...]]
print(results["metadatas"])  # [[{...}, {...}, ...]]
```

### With Pre-computed Embeddings

```python
results = collection.query(
    query_embeddings=[[0.1, 0.2, ...]],
    n_results=5
)
```

### Metadata Filtering

```python
# Equality
results = collection.query(
    query_texts=["query"],
    where={"source": "manual.pdf"}
)

# Comparison operators
results = collection.query(
    query_texts=["query"],
    where={"page": {"$gt": 10}}  # page > 10
)

# Logical operators
results = collection.query(
    query_texts=["query"],
    where={
        "$and": [
            {"source": "manual.pdf"},
            {"page": {"$lte": 50}}
        ]
    }
)

# In list
results = collection.query(
    query_texts=["query"],
    where={"category": {"$in": ["tech", "science"]}}
)
```

### Document Content Filtering

```python
results = collection.query(
    query_texts=["query"],
    where_document={"$contains": "specific phrase"}
)
```

### Include/Exclude Fields

```python
results = collection.query(
    query_texts=["query"],
    include=["documents", "metadatas", "distances"]  # exclude embeddings
)
```

## Collection Management

### List Collections

```python
collections = client.list_collections()
for col in collections:
    print(f"{col.name}: {col.count()} documents")
```

### Get Collection Info

```python
collection = client.get_collection(name="documents")
print(f"Count: {collection.count()}")
print(f"Metadata: {collection.metadata}")
```

### Delete Collection

```python
client.delete_collection(name="old_collection")
```

### Collection Settings

```python
from chromadb.config import Settings

collection = client.create_collection(
    name="custom_settings",
    metadata={
        "hnsw:space": "cosine",  # or "l2", "ip"
        "hnsw:construction_ef": 100,
        "hnsw:search_ef": 50,
        "hnsw:M": 16
    }
)
```

## LangChain Integration

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Create from documents
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="langchain_docs"
)

# Load existing
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="langchain_docs"
)

# Search
results = vectorstore.similarity_search("query", k=4)

# As retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
```

## Docker Deployment

```yaml
# docker-compose.yml
services:
  chroma:
    image: chromadb/chroma:latest
    container_name: chroma
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - ANONYMIZED_TELEMETRY=False
      - ALLOW_RESET=False

volumes:
  chroma_data:
```

```bash
docker compose up -d
```

## Performance Tips

### Batch Operations

```python
# Add in batches for large datasets
batch_size = 1000
for i in range(0, len(documents), batch_size):
    batch_docs = documents[i:i + batch_size]
    batch_ids = ids[i:i + batch_size]
    collection.add(documents=batch_docs, ids=batch_ids)
```

### Index Tuning

```python
# Higher M = better recall, more memory
# Higher ef = better recall, slower search
collection = client.create_collection(
    name="tuned",
    metadata={
        "hnsw:M": 32,              # Default: 16
        "hnsw:construction_ef": 200,  # Default: 100
        "hnsw:search_ef": 100      # Default: 10
    }
)
```

### Memory Management

```python
# For large collections, use persistent client
client = chromadb.PersistentClient(path="./db")

# Reset connection periodically for long-running processes
client.reset()
```

## Limitations

- Single-node only (no distributed mode)
- No GPU acceleration
- Limited to ~10M vectors efficiently
- Basic filtering compared to Qdrant/Milvus

## See Also

- [Vector Databases Overview](index.md)
- [Qdrant](qdrant.md) - For production workloads
- [RAG Implementation](../rag/implementation.md)
