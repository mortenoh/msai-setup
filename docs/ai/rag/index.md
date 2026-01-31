# RAG (Retrieval-Augmented Generation)

RAG combines the power of large language models with external knowledge retrieval, enabling accurate responses grounded in your own documents and data.

## Why RAG?

LLMs have knowledge cutoffs and can hallucinate. RAG solves this by:

- **Grounding responses** in actual documents
- **Reducing hallucinations** through factual retrieval
- **Keeping knowledge current** without retraining
- **Domain-specific expertise** from your own data

## Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Documents│───>│ Chunking │───>│Embeddings│              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                        │                    │
│                                        v                    │
│                               ┌──────────────┐              │
│                               │Vector Database│             │
│                               └──────────────┘              │
│                                        │                    │
│  ┌──────────┐    ┌──────────┐         │                    │
│  │  Query   │───>│ Retrieval│<────────┘                    │
│  └──────────┘    └──────────┘                              │
│                        │                                    │
│                        v                                    │
│               ┌──────────────┐    ┌──────────┐             │
│               │   Context    │───>│   LLM    │             │
│               │  Augmented   │    │ Response │             │
│               └──────────────┘    └──────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## In This Section

| Document | Description |
|----------|-------------|
| [Fundamentals](fundamentals.md) | Core concepts, chunking strategies, retrieval methods |
| [Implementation](implementation.md) | Building a RAG pipeline from scratch |
| [Optimization](optimization.md) | Improving retrieval quality and performance |
| [Integration](integration.md) | Connecting RAG to your applications |

## Quick Start

### Minimal RAG with LangChain

```python
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load documents
loader = DirectoryLoader("./docs", glob="**/*.md")
documents = loader.load()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# Create embeddings and store
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./db")

# Create retrieval chain
llm = Ollama(model="llama3.2")
qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

# Query
response = qa.invoke("What is the main topic of these documents?")
print(response["result"])
```

## Technology Stack

### Embedding Models (Local)

| Model | Dimensions | Use Case |
|-------|------------|----------|
| nomic-embed-text | 768 | General purpose, fast |
| mxbai-embed-large | 1024 | Higher quality, slower |
| all-minilm | 384 | Lightweight, mobile |
| bge-m3 | 1024 | Multilingual |

### Vector Databases

| Database | Best For |
|----------|----------|
| [ChromaDB](../vector-databases/chroma.md) | Local development, simplicity |
| [Qdrant](../vector-databases/qdrant.md) | Production, scalability |
| [Milvus](../vector-databases/milvus.md) | Large scale, enterprise |
| pgvector | PostgreSQL integration |

### LLM Integration

All local inference engines work with RAG:

- [Ollama](../inference-engines/ollama/index.md) - Easiest integration
- [llama.cpp](../inference-engines/llama-cpp/index.md) - Maximum performance
- [vLLM](../inference-engines/vllm/index.md) - High throughput serving

## See Also

- [Vector Databases](../vector-databases/index.md)
- [Embeddings Guide](../models/embeddings.md)
- [LangChain Integration](../agent-frameworks/langchain.md)
