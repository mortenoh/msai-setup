# RAG Fundamentals

Understanding the core concepts behind Retrieval-Augmented Generation.

## The RAG Process

### 1. Document Ingestion

Transform raw documents into searchable chunks:

```
Raw Documents → Parsing → Cleaning → Chunking → Embedding → Storage
```

**Supported formats:**
- Text: `.txt`, `.md`, `.rst`
- Documents: `.pdf`, `.docx`, `.pptx`
- Code: `.py`, `.js`, `.ts`, etc.
- Data: `.json`, `.csv`, `.xml`

### 2. Chunking Strategies

How you split documents significantly impacts retrieval quality.

#### Fixed-Size Chunking

Simple but can break context:

```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separator="\n"
)
```

#### Recursive Chunking (Recommended)

Respects document structure:

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

#### Semantic Chunking

Groups by meaning, not size:

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")
splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
```

#### Code-Aware Chunking

For codebases:

```python
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=2000,
    chunk_overlap=200
)
```

### Chunk Size Guidelines

| Content Type | Chunk Size | Overlap |
|--------------|------------|---------|
| General text | 500-1000 | 100-200 |
| Technical docs | 1000-1500 | 200-300 |
| Code | 1500-2000 | 200-400 |
| Q&A/FAQ | 200-500 | 50-100 |

## Embeddings

### What Are Embeddings?

Numerical representations of text that capture semantic meaning:

```
"The cat sat on the mat" → [0.23, -0.45, 0.12, ..., 0.89]
                           └─────── 768 dimensions ───────┘
```

Similar meanings produce similar vectors, enabling semantic search.

### Local Embedding Models

```bash
# Pull embedding models with Ollama
ollama pull nomic-embed-text
ollama pull mxbai-embed-large
ollama pull all-minilm
```

### Using Embeddings

```python
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Single text
vector = embeddings.embed_query("What is machine learning?")
print(f"Dimensions: {len(vector)}")  # 768

# Batch embedding
vectors = embeddings.embed_documents([
    "Machine learning is...",
    "Deep learning uses...",
    "Neural networks are..."
])
```

## Retrieval Methods

### Similarity Search

Find the k most similar documents:

```python
# Basic similarity search
docs = vectorstore.similarity_search(query, k=4)

# With score threshold
docs = vectorstore.similarity_search_with_score(query, k=4)
relevant = [(doc, score) for doc, score in docs if score > 0.7]
```

### Maximum Marginal Relevance (MMR)

Balance relevance with diversity:

```python
docs = vectorstore.max_marginal_relevance_search(
    query,
    k=4,
    fetch_k=20,      # Fetch more, then diversify
    lambda_mult=0.5  # 0=max diversity, 1=max relevance
)
```

### Hybrid Search

Combine semantic and keyword search:

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# Keyword-based retriever
bm25 = BM25Retriever.from_documents(documents)
bm25.k = 4

# Semantic retriever
semantic = vectorstore.as_retriever(search_kwargs={"k": 4})

# Combine with weights
hybrid = EnsembleRetriever(
    retrievers=[bm25, semantic],
    weights=[0.3, 0.7]
)
```

## Context Window Management

### The Challenge

LLMs have limited context windows. You must fit:
- System prompt
- Retrieved documents
- User query
- Space for response

### Strategies

#### 1. Limit Retrieved Chunks

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # Fewer, more relevant chunks
)
```

#### 2. Compress Retrieved Content

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)
```

#### 3. Rerank Results

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import CohereRerank

# Or use local reranker
reranker = CohereRerank(top_n=3)
rerank_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=retriever
)
```

## Prompt Engineering for RAG

### Basic RAG Prompt

```python
template = """Use the following context to answer the question.
If the answer is not in the context, say "I don't know."

Context:
{context}

Question: {question}

Answer:"""
```

### Structured RAG Prompt

```python
template = """You are a helpful assistant answering questions based on provided documentation.

INSTRUCTIONS:
1. Only use information from the context below
2. If the context doesn't contain the answer, say so
3. Cite sources when possible
4. Be concise but complete

CONTEXT:
{context}

USER QUESTION: {question}

ANSWER:"""
```

## Evaluation Metrics

### Retrieval Quality

| Metric | Description |
|--------|-------------|
| Precision@k | Relevant docs in top k results |
| Recall@k | Relevant docs retrieved vs total relevant |
| MRR | Mean Reciprocal Rank of first relevant result |
| NDCG | Normalized Discounted Cumulative Gain |

### Generation Quality

| Metric | Description |
|--------|-------------|
| Faithfulness | Is the answer grounded in context? |
| Answer relevance | Does it answer the question? |
| Context relevance | Was the right context retrieved? |

### RAGAS Evaluation

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision]
)
print(result)
```

## Common Pitfalls

### 1. Chunks Too Large
- Retrieves irrelevant content
- Wastes context window
- **Fix:** Smaller chunks with overlap

### 2. Chunks Too Small
- Loses context
- Fragments information
- **Fix:** Larger chunks or parent document retrieval

### 3. Poor Embedding Model Choice
- Misses semantic matches
- Language mismatch
- **Fix:** Use domain-appropriate embeddings

### 4. Ignoring Metadata
- Can't filter by source, date, etc.
- **Fix:** Store and use document metadata

```python
doc = Document(
    page_content="...",
    metadata={
        "source": "manual.pdf",
        "page": 42,
        "date": "2024-01-15"
    }
)
```

## See Also

- [Implementation Guide](implementation.md)
- [Vector Databases](../vector-databases/index.md)
- [Optimization Techniques](optimization.md)
