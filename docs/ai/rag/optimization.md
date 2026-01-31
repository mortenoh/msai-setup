# RAG Optimization

Techniques to improve retrieval quality, reduce latency, and enhance answer accuracy.

## Retrieval Optimization

### Chunking Improvements

#### Parent Document Retrieval

Retrieve small chunks but return larger context:

```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Small chunks for precise retrieval
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

# Larger chunks for context
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)

store = InMemoryStore()

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

# Add documents (stores both parent and child chunks)
retriever.add_documents(documents)

# Retrieval returns parent documents
docs = retriever.invoke("query")
```

#### Multi-Vector Retrieval

Generate multiple representations per document:

```python
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore
import uuid

# Store for full documents
docstore = InMemoryStore()

retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    id_key="doc_id",
)

# Generate summary embeddings alongside content
for doc in documents:
    doc_id = str(uuid.uuid4())

    # Store original
    docstore.mset([(doc_id, doc)])

    # Create summary
    summary = llm.invoke(f"Summarize: {doc.page_content}")
    summary_doc = Document(
        page_content=summary,
        metadata={"doc_id": doc_id}
    )

    # Add summary to vectorstore
    retriever.vectorstore.add_documents([summary_doc])
```

### Hybrid Search

Combine dense (semantic) and sparse (keyword) retrieval:

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# Sparse retriever (keyword-based)
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 4

# Dense retriever (semantic)
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Ensemble with weights
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, dense_retriever],
    weights=[0.4, 0.6]  # Favor semantic but include keyword
)
```

### Reranking

Second-pass scoring for better precision:

```python
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list, top_k: int = 4):
        # Score all documents
        pairs = [[query, doc.page_content] for doc in documents]
        scores = self.model.predict(pairs)

        # Sort by score
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, score in scored_docs[:top_k]]

# Usage
reranker = Reranker()
initial_docs = retriever.invoke(query)  # Get more than needed
reranked_docs = reranker.rerank(query, initial_docs, top_k=4)
```

### Query Transformation

#### Query Expansion

Generate multiple query variations:

```python
from langchain_core.prompts import PromptTemplate

expansion_prompt = PromptTemplate.from_template("""
Generate 3 alternative versions of this question to improve search results.
Each version should capture the same intent but use different words.

Original question: {question}

Alternative questions (one per line):""")

def expand_query(question: str) -> list[str]:
    response = llm.invoke(expansion_prompt.format(question=question))
    alternatives = response.strip().split("\n")
    return [question] + alternatives[:3]

# Retrieve with all variations
def multi_query_retrieve(question: str, k: int = 4) -> list:
    queries = expand_query(question)
    all_docs = []

    for q in queries:
        docs = retriever.invoke(q)
        all_docs.extend(docs)

    # Deduplicate
    seen = set()
    unique_docs = []
    for doc in all_docs:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            unique_docs.append(doc)

    return unique_docs[:k]
```

#### HyDE (Hypothetical Document Embeddings)

Generate a hypothetical answer and use it for retrieval:

```python
hyde_prompt = PromptTemplate.from_template("""
Write a paragraph that would answer this question:
{question}

Paragraph:""")

def hyde_retrieve(question: str, k: int = 4):
    # Generate hypothetical answer
    hypothetical = llm.invoke(hyde_prompt.format(question=question))

    # Use hypothetical answer for retrieval
    return vectorstore.similarity_search(hypothetical, k=k)
```

## Performance Optimization

### Embedding Caching

Cache embeddings to avoid recomputation:

```python
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore

# Create cache
store = LocalFileStore("./embedding_cache")

# Wrap embeddings with cache
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings=embeddings,
    document_embedding_cache=store,
    namespace="nomic-embed-text"
)
```

### Batch Processing

Embed documents in batches:

```python
def batch_embed(documents: list, batch_size: int = 100):
    all_ids = []

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        ids = vectorstore.add_documents(batch)
        all_ids.extend(ids)
        print(f"Processed {min(i + batch_size, len(documents))}/{len(documents)}")

    return all_ids
```

### Async Operations

Use async for concurrent operations:

```python
import asyncio
from langchain_community.embeddings import OllamaEmbeddings

async def async_embed_documents(texts: list[str]) -> list[list[float]]:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Embed in parallel batches
    batch_size = 10
    tasks = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        task = asyncio.create_task(
            asyncio.to_thread(embeddings.embed_documents, batch)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return [emb for batch in results for emb in batch]
```

### Memory Management

For large document sets:

```python
def stream_ingest(documents_dir: Path, batch_size: int = 50):
    """Stream documents to avoid memory issues."""
    from pathlib import Path
    import gc

    files = list(documents_dir.glob("**/*.pdf"))

    for i in range(0, len(files), batch_size):
        batch_files = files[i:i + batch_size]
        documents = []

        for file in batch_files:
            docs = loader.load_file(file)
            documents.extend(docs)

        chunks = chunker.chunk(documents)
        vectorstore.add_documents(chunks)

        # Clear memory
        del documents, chunks
        gc.collect()

        print(f"Ingested {min(i + batch_size, len(files))}/{len(files)} files")
```

## Quality Improvements

### Metadata Filtering

Add and use metadata for precise retrieval:

```python
# During ingestion
for doc in documents:
    doc.metadata["category"] = classify_document(doc)
    doc.metadata["date"] = extract_date(doc)
    doc.metadata["author"] = extract_author(doc)

vectorstore.add_documents(documents)

# During retrieval
docs = vectorstore.similarity_search(
    query,
    k=4,
    filter={"category": "technical", "date": {"$gte": "2024-01-01"}}
)
```

### Context Enrichment

Add surrounding context to chunks:

```python
def enrich_chunks(chunks: list) -> list:
    """Add context from neighboring chunks."""
    enriched = []

    for i, chunk in enumerate(chunks):
        context_parts = []

        # Add previous chunk summary
        if i > 0:
            prev_summary = summarize(chunks[i-1].page_content)
            context_parts.append(f"Previous: {prev_summary}")

        context_parts.append(chunk.page_content)

        # Add next chunk summary
        if i < len(chunks) - 1:
            next_summary = summarize(chunks[i+1].page_content)
            context_parts.append(f"Next: {next_summary}")

        enriched_content = "\n\n".join(context_parts)
        enriched.append(Document(
            page_content=enriched_content,
            metadata=chunk.metadata
        ))

    return enriched
```

### Answer Verification

Verify answers against sources:

```python
verification_prompt = PromptTemplate.from_template("""
Given the following context and answer, determine if the answer is:
1. SUPPORTED - fully supported by the context
2. PARTIAL - partially supported
3. UNSUPPORTED - not supported by the context

Context:
{context}

Answer:
{answer}

Evaluation (respond with just SUPPORTED, PARTIAL, or UNSUPPORTED):""")

def verify_answer(context: str, answer: str) -> str:
    result = llm.invoke(verification_prompt.format(
        context=context,
        answer=answer
    ))
    return result.strip()
```

## Monitoring

### Metrics to Track

```python
import time
from dataclasses import dataclass

@dataclass
class QueryMetrics:
    query: str
    retrieval_time: float
    generation_time: float
    total_time: float
    num_docs_retrieved: int
    tokens_used: int

def tracked_query(question: str) -> tuple[str, QueryMetrics]:
    start = time.time()

    # Retrieval
    retrieval_start = time.time()
    docs = retriever.invoke(question)
    retrieval_time = time.time() - retrieval_start

    # Generation
    generation_start = time.time()
    answer = chain.invoke(question)
    generation_time = time.time() - generation_start

    metrics = QueryMetrics(
        query=question,
        retrieval_time=retrieval_time,
        generation_time=generation_time,
        total_time=time.time() - start,
        num_docs_retrieved=len(docs),
        tokens_used=len(answer.split()) * 1.3  # Rough estimate
    )

    return answer, metrics
```

### Logging

```python
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag")

def log_query(question: str, answer: str, metrics: QueryMetrics):
    logger.info(json.dumps({
        "event": "query",
        "question": question[:100],
        "answer_length": len(answer),
        "retrieval_ms": metrics.retrieval_time * 1000,
        "generation_ms": metrics.generation_time * 1000,
        "docs_retrieved": metrics.num_docs_retrieved,
    }))
```

## See Also

- [Fundamentals](fundamentals.md)
- [Implementation Guide](implementation.md)
- [Vector Databases](../vector-databases/index.md)
