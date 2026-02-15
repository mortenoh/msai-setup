# Dify

Open-source platform for building AI applications with a visual workflow editor.

## Overview

- Purpose-built AI application platform
- App types: Chatbot, Text Generator, Agent, Workflow
- Built-in RAG with knowledge base management
- Visual workflow editor with LLM, code, conditional, and tool nodes
- Model provider abstraction (Ollama, OpenAI, Anthropic, local models)
- Observability: token usage, latency, user feedback tracking
- Apache-2.0 license (core)

## Installation

### Docker Compose

```bash
git clone https://github.com/langgenius/dify.git
cd dify/docker
cp .env.example .env
docker compose up -d
```

Access Dify at `http://localhost` (port 80). On first visit, create an admin account.

The default stack includes:

- **Dify API** -- backend service
- **Dify Web** -- frontend UI
- **PostgreSQL** -- metadata storage
- **Redis** -- caching and message queue
- **Weaviate** -- default vector database (can be changed)
- **Nginx** -- reverse proxy

### Ollama Integration

1. Go to **Settings** > **Model Providers**
2. Find **Ollama** and click **Configure**
3. Set **Base URL**:
    - Docker (same host): `http://host.docker.internal:11434`
    - Linux Docker (bridge): use the host's Docker bridge IP (e.g., `http://172.17.0.1:11434`)
    - Native install: `http://localhost:11434`
4. Click **Save**
5. Add models:
    - Click **Add Model**
    - Enter the exact model name as shown in `ollama list` (e.g., `llama3.3`, `deepseek-r1:14b`)
    - Select model type: **LLM** or **Text Embedding**
    - Set context size to match the model's capability

For embeddings, add a separate model entry:

- Model name: `nomic-embed-text`
- Model type: **Text Embedding**

## App Types

### Chatbot

Conversational AI with context memory:

1. Click **Create App** > **Chatbot**
2. Select an Ollama model as the LLM
3. Configure:
    - **System prompt** -- define the assistant's behavior
    - **Opening remarks** -- greeting message shown to users
    - **Suggested questions** -- clickable prompts for users
    - **Knowledge base** -- attach documents for RAG (see below)
4. Publish and share via URL or embed in a website

### Workflow

Visual DAG editor for multi-step AI pipelines:

1. Click **Create App** > **Workflow**
2. Build a pipeline using node types:
    - **Start** -- input variables and trigger
    - **LLM** -- call a language model with a prompt template
    - **Code** -- run Python or JavaScript
    - **Conditional** -- branch based on variable values
    - **HTTP Request** -- call external APIs
    - **Template** -- format text with Jinja2 templates
    - **Variable Aggregator** -- combine outputs from parallel branches
    - **Iteration** -- loop over list items
    - **End** -- define output variables
3. Connect nodes by dragging edges between them
4. Variables pass between nodes via `{{node_name.output_variable}}` syntax

### Agent

Autonomous AI with tool use:

1. Click **Create App** > **Agent**
2. Select reasoning mode:
    - **Function Calling** -- structured tool invocation (recommended for capable models)
    - **ReAct** -- reasoning + acting loop (works with all models)
3. Add tools:
    - **Built-in** -- web search, calculator, Wikipedia, current time
    - **Custom** -- define API tools via OpenAPI schema
    - **Workflow as tool** -- use a Dify workflow as an agent tool
4. Configure max iterations and other agent parameters

## Knowledge Base (RAG)

Upload and index documents for retrieval-augmented generation:

1. Go to **Knowledge** in the sidebar
2. Click **Create Knowledge Base**
3. Upload documents (supported formats: PDF, TXT, MD, DOCX, CSV, HTML)
4. Configure processing:
    - **Chunking** -- automatic or custom chunk size/overlap
    - **Embedding model** -- select an Ollama embedding model (e.g., `nomic-embed-text`)
    - **Indexing mode** -- high quality (vector + keyword) or economical (keyword only)
5. Wait for indexing to complete

### Retrieval Modes

| Mode | Description | Best For |
|------|-------------|----------|
| Vector search | Semantic similarity via embeddings | General questions |
| Keyword search | Full-text keyword matching | Exact term lookups |
| Hybrid search | Combined vector + keyword with reranking | Best overall accuracy |

### Connect to Apps

1. Open your Chatbot or Agent app
2. In the **Context** section, click **Add**
3. Select your knowledge base
4. Configure retrieval parameters:
    - **Top K** -- number of chunks to retrieve (default: 3)
    - **Score threshold** -- minimum relevance score

## API Access

Every Dify app gets a REST API automatically:

1. Open your app and go to **Access API** in the left sidebar
2. Create an API key
3. Use the documented endpoints:

```bash
# Chat endpoint (for Chatbot and Agent apps)
curl -X POST 'http://localhost/v1/chat-messages' \
  -H 'Authorization: Bearer app-YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {},
    "query": "What is the capital of France?",
    "response_mode": "blocking",
    "conversation_id": "",
    "user": "user-123"
  }'
```

```bash
# Workflow endpoint
curl -X POST 'http://localhost/v1/workflows/run' \
  -H 'Authorization: Bearer app-YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {"topic": "machine learning"},
    "response_mode": "blocking",
    "user": "user-123"
  }'
```

Response modes:

- `blocking` -- wait for full response
- `streaming` -- receive Server-Sent Events as the response is generated

## Configuration

### Environment Variables

Key variables in `docker/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret for encryption | generated |
| `DB_USERNAME` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `difyai123456` |
| `REDIS_PASSWORD` | Redis password | `difyai123456` |
| `STORAGE_TYPE` | File storage backend (`local`, `s3`) | `local` |
| `VECTOR_STORE` | Vector DB (`weaviate`, `qdrant`, `milvus`, `pgvector`) | `weaviate` |
| `OLLAMA_BASE_URL` | Default Ollama URL | -- |

!!! warning "Change default passwords"
    Update `DB_PASSWORD`, `REDIS_PASSWORD`, and `SECRET_KEY` before any production use.

### Persistent Storage

The default Compose file creates named volumes for all data. For custom paths:

```yaml
volumes:
  - /tank/ai/dify/storage:/app/api/storage
  - /tank/ai/dify/db:/var/lib/postgresql/data
```

### Reverse Proxy

Dify includes Nginx. To use an external reverse proxy (Caddy or Traefik), expose the API and web services directly:

```yaml
services:
  api:
    ports:
      - "5001:5001"
  web:
    ports:
      - "3000:3000"
```

Then proxy `/v1/*` and `/console/*` to port 5001, and everything else to port 3000.

## Troubleshooting

### Ollama connection from Docker

If Dify cannot reach Ollama:

- **macOS/Windows Docker Desktop**: use `http://host.docker.internal:11434`
- **Linux Docker**: use the host bridge IP:

```bash
# Find Docker bridge IP
ip addr show docker0 | grep inet
# Usually 172.17.0.1
```

- Ensure Ollama is listening on all interfaces:

```bash
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

### Model not appearing

- The model name in Dify must exactly match the output of `ollama list`
- Include the tag if it is not `latest` (e.g., `deepseek-r1:14b` not just `deepseek-r1`)

### Knowledge base indexing failures

- Check that your embedding model is running in Ollama: `ollama run nomic-embed-text`
- For large documents, increase the Celery worker timeout in `.env`
- Monitor logs: `docker compose logs -f api`

### Memory usage

- Each knowledge base creates an index in the vector database
- Monitor vector DB memory: `docker stats`
- For large knowledge bases (10k+ documents), consider switching to Qdrant or Milvus

## See Also

- [Ollama](../inference-engines/ollama.md) -- local LLM inference
- [RAG Fundamentals](../rag/fundamentals.md) -- retrieval-augmented generation concepts
- [Vector Databases](../vector-databases/index.md) -- Qdrant, Milvus, ChromaDB
- [Open WebUI](../gui-tools/open-webui.md) -- alternative chat interface
- [AI Automation Overview](index.md) -- platform comparison
