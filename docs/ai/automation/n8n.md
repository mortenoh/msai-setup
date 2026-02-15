# n8n

Self-hosted workflow automation platform with AI agent capabilities.

## Overview

- 400+ integrations (Slack, email, GitHub, databases, HTTP APIs)
- AI nodes: AI Agent, Text Classifier, Information Extractor, Summarizer
- Native Ollama integration for chat and embedding models
- Visual workflow builder with branching, loops, error handling
- Webhook triggers, scheduled runs, event-driven workflows
- Fair-code license (free self-hosted, source-available)

## Installation

### Docker Compose (AI Starter Kit)

Full stack with n8n, Ollama, Qdrant, and PostgreSQL based on the official `n8n-io/self-hosted-ai-starter-kit`:

```yaml
# docker-compose.yml
services:
  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_DIAGNOSTICS_ENABLED=false
      - N8N_PERSONALIZATION_ENABLED=false
    volumes:
      - n8n-data:/home/node/.n8n
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=n8n
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U n8n"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    restart: unless-stopped
    ports:
      - "6333:6333"
    volumes:
      - qdrant-data:/qdrant/storage

volumes:
  n8n-data:
  postgres-data:
  qdrant-data:
```

```bash
# Generate encryption key
echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)" >> .env

docker compose up -d
```

Access n8n at `http://localhost:5678` and create your admin account.

### Docker Compose (Standalone)

Minimal setup when you already have Ollama running:

```yaml
# docker-compose.yml
services:
  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - n8n-data:/home/node/.n8n

volumes:
  n8n-data:
```

This uses the built-in SQLite database. Suitable for personal use and experimentation.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `N8N_ENCRYPTION_KEY` | Encrypts credentials at rest (required) | -- |
| `DB_TYPE` | Database backend (`sqlite`, `postgresdb`) | `sqlite` |
| `DB_POSTGRESDB_HOST` | PostgreSQL host | `localhost` |
| `DB_POSTGRESDB_DATABASE` | Database name | `n8n` |
| `N8N_DIAGNOSTICS_ENABLED` | Send usage telemetry | `true` |
| `WEBHOOK_URL` | External webhook URL | auto-detected |
| `N8N_PORT` | HTTP port | `5678` |

### Ollama Credentials

1. Go to **Settings** > **Credentials** > **Add Credential**
2. Search for **Ollama**
3. Set **Base URL**:
    - Docker (same Compose network): `http://ollama:11434`
    - Docker (host Ollama): `http://host.docker.internal:11434`
    - Native install: `http://localhost:11434`

## AI Workflows

### AI Agent Node

The AI Agent node connects an LLM to tools, memory, and output parsers:

1. Add an **AI Agent** node to your workflow
2. Connect an **Ollama Chat Model** sub-node:
    - Select your Ollama credential
    - Choose a model (e.g., `llama3.3`, `qwen2.5`)
3. Add tools (optional):
    - **HTTP Request** -- call external APIs
    - **Code** -- execute JavaScript/Python
    - **Postgres** / **MySQL** -- query databases
    - **Vector Store** -- search Qdrant/Chroma for RAG
4. Add memory (optional):
    - **Window Buffer Memory** -- last N messages
    - **Qdrant Vector Store Memory** -- long-term recall
5. Set a **System Message** to define the agent's behavior

### Text Classification

Categorize input data using an LLM:

1. Add a **Text Classifier** node
2. Connect an **Ollama Chat Model** sub-node
3. Define categories (e.g., `support`, `billing`, `feature-request`)
4. The node outputs the matched category for downstream routing

Example use cases:

- Classify incoming support tickets and route to the right team
- Categorize emails before processing
- Tag incoming webhook data

### RAG with Qdrant

#### Document Ingestion Workflow

Build a workflow to load, chunk, embed, and store documents:

1. **Read Binary File** or **HTTP Request** -- load document
2. **Extract Document Text** -- extract text from PDF/DOCX
3. **Recursive Character Text Splitter** -- chunk text
4. **Embeddings Ollama** -- generate embeddings (`nomic-embed-text`)
5. **Qdrant Vector Store (Insert)** -- store chunks with embeddings

#### Query Workflow

Answer questions using stored documents:

1. **Webhook** or **Chat Trigger** -- receive question
2. **AI Agent** node with:
    - **Ollama Chat Model** as LLM
    - **Vector Store Tool** pointing to Qdrant collection
3. **Respond to Webhook** -- return the answer

### Example: Document Q&A Bot

Step-by-step workflow:

1. Create a new workflow
2. Add a **Chat Trigger** node (provides built-in chat UI)
3. Add an **AI Agent** node and connect it to the trigger
4. Under the AI Agent, add:
    - **Ollama Chat Model** -- select `llama3.3`
    - **Vector Store Tool** -- connect to your Qdrant collection
    - **Window Buffer Memory** -- keep last 10 messages
5. Set the system message:

    ```
    You are a helpful assistant that answers questions based on the provided documents.
    Always cite which document your answer comes from.
    If you don't know the answer, say so.
    ```

6. Click **Chat** to test in the built-in chat panel

## Troubleshooting

### Ollama connection issues in Docker

If n8n cannot reach Ollama:

```bash
# Verify Ollama is accessible from the n8n container
docker exec -it n8n-n8n-1 wget -qO- http://host.docker.internal:11434/api/tags
```

If using separate Compose files, create a shared Docker network:

```bash
docker network create ai-network
```

Then add to both Compose files:

```yaml
networks:
  default:
    external: true
    name: ai-network
```

### Timeout on large model responses

For models that generate long responses, increase the HTTP timeout:

- In the Ollama credential settings, set a longer timeout
- Or set `OLLAMA_KEEP_ALIVE` to a longer duration on the Ollama side

### Workflow execution errors

- Check the execution log: **Executions** tab in the left sidebar
- Each node shows its input/output data -- click a failed node to inspect
- Enable **Error Trigger** node to catch and handle failures

## See Also

- [Ollama](../inference-engines/ollama.md) -- local LLM inference
- [Qdrant](../vector-databases/qdrant.md) -- vector database for RAG
- [Agent Frameworks](../agent-frameworks/index.md) -- code-based agent tools
- [AI Automation Overview](index.md) -- platform comparison
