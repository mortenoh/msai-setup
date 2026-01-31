# RAG Implementation Guide

Step-by-step guide to building a production-ready RAG pipeline.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Production RAG Stack                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Ingestion │  │   Serving   │  │       Monitoring        │ │
│  │   Pipeline  │  │    Layer    │  │                         │ │
│  │             │  │             │  │  - Query latency        │ │
│  │ - Loaders   │  │ - FastAPI   │  │  - Retrieval quality    │ │
│  │ - Chunkers  │  │ - Streaming │  │  - Token usage          │ │
│  │ - Embedders │  │ - Caching   │  │  - Error rates          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│         │                │                                      │
│         v                v                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Vector Database                          ││
│  │                      (ChromaDB)                             ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                │                                      │
│         v                v                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   LLM (Ollama)                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Project Setup

### Directory Structure

```
rag-project/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loaders.py
│   │   ├── chunkers.py
│   │   └── embedders.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── vectorstore.py
│   │   └── retrievers.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── llm.py
│   │   └── chains.py
│   └── api/
│       ├── __init__.py
│       └── server.py
├── data/
│   ├── documents/
│   └── vectordb/
├── tests/
├── pyproject.toml
└── docker-compose.yml
```

### Dependencies

```toml
# pyproject.toml
[project]
name = "rag-pipeline"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "langchain>=0.1.0",
    "langchain-community>=0.0.20",
    "chromadb>=0.4.0",
    "ollama>=0.1.0",
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "python-multipart>=0.0.6",
    "pypdf>=4.0.0",
    "unstructured>=0.12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ragas>=0.1.0",
]
```

## Implementation

### Configuration

```python
# src/config.py
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Paths
    documents_dir: Path = Path("data/documents")
    vectordb_dir: Path = Path("data/vectordb")

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Embedding
    embedding_model: str = "nomic-embed-text"

    # LLM
    llm_model: str = "llama3.2"
    llm_base_url: str = "http://localhost:11434"

    # Retrieval
    retrieval_k: int = 4

    # ChromaDB
    collection_name: str = "documents"

    class Config:
        env_prefix = "RAG_"

settings = Settings()
```

### Document Loaders

```python
# src/ingestion/loaders.py
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

class DocumentLoader:
    """Load documents from various sources."""

    LOADERS = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".md": UnstructuredMarkdownLoader,
    }

    def __init__(self, documents_dir: Path):
        self.documents_dir = documents_dir

    def load_all(self) -> List[Document]:
        """Load all documents from the directory."""
        documents = []

        for ext, loader_cls in self.LOADERS.items():
            loader = DirectoryLoader(
                str(self.documents_dir),
                glob=f"**/*{ext}",
                loader_cls=loader_cls,
                show_progress=True,
            )
            documents.extend(loader.load())

        return documents

    def load_file(self, file_path: Path) -> List[Document]:
        """Load a single file."""
        ext = file_path.suffix.lower()
        loader_cls = self.LOADERS.get(ext)

        if not loader_cls:
            raise ValueError(f"Unsupported file type: {ext}")

        loader = loader_cls(str(file_path))
        return loader.load()
```

### Chunking

```python
# src/ingestion/chunkers.py
from typing import List
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentChunker:
    """Split documents into chunks."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        return self.splitter.split_documents(documents)

    def chunk_with_metadata(
        self,
        documents: List[Document],
        add_chunk_index: bool = True
    ) -> List[Document]:
        """Split documents and enrich metadata."""
        chunks = self.splitter.split_documents(documents)

        if add_chunk_index:
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["chunk_total"] = len(chunks)

        return chunks
```

### Vector Store

```python
# src/retrieval/vectorstore.py
from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document

class VectorStore:
    """Manage vector storage and retrieval."""

    def __init__(
        self,
        persist_directory: Path,
        collection_name: str,
        embedding_model: str = "nomic-embed-text",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        self.embeddings = OllamaEmbeddings(model=embedding_model)

        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self._vectorstore: Optional[Chroma] = None

    @property
    def vectorstore(self) -> Chroma:
        """Get or create the vectorstore."""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
        return self._vectorstore

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vectorstore."""
        return self.vectorstore.add_documents(documents)

    def search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
    ) -> List[Document]:
        """Search for similar documents."""
        return self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter,
        )

    def search_with_scores(
        self,
        query: str,
        k: int = 4,
    ) -> List[tuple[Document, float]]:
        """Search with relevance scores."""
        return self.vectorstore.similarity_search_with_score(query, k=k)

    def delete_collection(self):
        """Delete the collection."""
        self.client.delete_collection(self.collection_name)
        self._vectorstore = None
```

### RAG Chain

```python
# src/generation/chains.py
from typing import Optional
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from ..retrieval.vectorstore import VectorStore

RAG_PROMPT = PromptTemplate.from_template("""
You are a helpful assistant answering questions based on the provided context.

INSTRUCTIONS:
- Only use information from the context below
- If the context doesn't contain the answer, say "I don't have enough information to answer that."
- Be concise but complete
- Cite the source document when relevant

CONTEXT:
{context}

QUESTION: {question}

ANSWER:""")


class RAGChain:
    """RAG question-answering chain."""

    def __init__(
        self,
        vectorstore: VectorStore,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        k: int = 4,
    ):
        self.vectorstore = vectorstore
        self.k = k

        self.llm = Ollama(
            model=model,
            base_url=base_url,
        )

        self.retriever = vectorstore.vectorstore.as_retriever(
            search_kwargs={"k": k}
        )

    def _format_docs(self, docs) -> str:
        """Format retrieved documents."""
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            formatted.append(f"[{i}] Source: {source}\n{doc.page_content}")
        return "\n\n---\n\n".join(formatted)

    def create_chain(self):
        """Create the RAG chain."""
        return (
            {
                "context": self.retriever | self._format_docs,
                "question": RunnablePassthrough(),
            }
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )

    def query(self, question: str) -> str:
        """Query the RAG system."""
        chain = self.create_chain()
        return chain.invoke(question)

    def query_with_sources(self, question: str) -> dict:
        """Query and return sources."""
        docs = self.retriever.invoke(question)
        answer = self.query(question)

        return {
            "answer": answer,
            "sources": [
                {
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata,
                }
                for doc in docs
            ],
        }
```

### FastAPI Server

```python
# src/api/server.py
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from ..config import settings
from ..ingestion.loaders import DocumentLoader
from ..ingestion.chunkers import DocumentChunker
from ..retrieval.vectorstore import VectorStore
from ..generation.chains import RAGChain

app = FastAPI(title="RAG API")

# Initialize components
vectorstore = VectorStore(
    persist_directory=settings.vectordb_dir,
    collection_name=settings.collection_name,
    embedding_model=settings.embedding_model,
)

rag_chain = RAGChain(
    vectorstore=vectorstore,
    model=settings.llm_model,
    k=settings.retrieval_k,
)


class QueryRequest(BaseModel):
    question: str
    k: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG system."""
    try:
        result = rag_chain.query_with_sources(request.question)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
async def ingest_documents():
    """Ingest all documents from the documents directory."""
    loader = DocumentLoader(settings.documents_dir)
    chunker = DocumentChunker(settings.chunk_size, settings.chunk_overlap)

    documents = loader.load_all()
    chunks = chunker.chunk(documents)
    ids = vectorstore.add_documents(chunks)

    return {
        "documents_loaded": len(documents),
        "chunks_created": len(chunks),
        "ids": ids[:5],  # Return first 5 IDs
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a single document."""
    # Save file temporarily
    temp_path = settings.documents_dir / file.filename
    content = await file.read()
    temp_path.write_bytes(content)

    # Process
    loader = DocumentLoader(settings.documents_dir)
    chunker = DocumentChunker(settings.chunk_size, settings.chunk_overlap)

    documents = loader.load_file(temp_path)
    chunks = chunker.chunk(documents)
    ids = vectorstore.add_documents(chunks)

    return {
        "filename": file.filename,
        "chunks_created": len(chunks),
    }


@app.delete("/collection")
async def delete_collection():
    """Delete the vector collection."""
    vectorstore.delete_collection()
    return {"status": "deleted"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}
```

## Docker Compose Setup

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  rag-api:
    build: .
    container_name: rag-api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - RAG_LLM_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

volumes:
  ollama_data:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install .

# Copy source
COPY src/ src/

# Run
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Running the Pipeline

### 1. Start Services

```bash
# Start Ollama and pull models
docker compose up -d ollama
docker exec ollama ollama pull llama3.2
docker exec ollama ollama pull nomic-embed-text

# Start RAG API
docker compose up -d rag-api
```

### 2. Ingest Documents

```bash
# Add documents to data/documents/
cp your-docs/* data/documents/

# Trigger ingestion
curl -X POST http://localhost:8000/ingest
```

### 3. Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main topics covered?"}'
```

## See Also

- [Optimization Guide](optimization.md)
- [Vector Databases](../vector-databases/index.md)
- [Ollama Integration](../inference-engines/ollama/index.md)
