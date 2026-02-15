# AI Automation

Visual platforms for building AI workflows and applications without writing code.

## Overview

- **Visual workflow builders** -- drag-and-drop interfaces for constructing AI pipelines
- **Local LLM backends** -- connect to Ollama and other local inference engines
- **Self-hosted Docker deployment** -- run everything on your own hardware
- **No-code/low-code** -- build AI applications without deep programming knowledge

!!! info "Agent Frameworks vs AI Automation"
    The [Agent Frameworks](../agent-frameworks/index.md) section covers code-based tools like
    LangChain, LangGraph, and CrewAI. This section covers visual, low-code platforms that
    provide browser-based interfaces for building AI workflows.

## Platform Comparison

| Feature | n8n | Dify |
|---------|-----|------|
| **Primary purpose** | General workflow automation | AI application platform |
| **AI capabilities** | AI Agent, Text Classifier, Summarizer nodes | Chatbot, Agent, Workflow, Text Generator apps |
| **Ollama integration** | Native Ollama credential + chat nodes | Model provider setting |
| **RAG** | Via Qdrant/Pinecone/Chroma vector store nodes | Built-in knowledge base with chunking and retrieval |
| **Visual editor** | Workflow canvas with 400+ integration nodes | DAG workflow editor with LLM/code/conditional nodes |
| **Multi-user** | Yes (community edition) | Yes |
| **API** | Webhook triggers, REST endpoints | RESTful API for all app types |
| **License** | Sustainable Use License (free self-hosted) | Apache-2.0 (core) |
| **Deployment** | Docker Compose | Docker Compose |

## Recommendation by Use Case

| Use Case | Recommended |
|----------|-------------|
| AI-powered automations (email, Slack, webhooks) | n8n |
| Building chatbots and AI apps | Dify |
| RAG applications with knowledge bases | Dify |
| Multi-step workflows with non-AI steps | n8n |
| Prototyping AI agents | Either |
| Connecting 400+ third-party services | n8n |
| LLM observability and usage tracking | Dify |

## In This Section

| Document | Description |
|----------|-------------|
| [n8n](n8n.md) | Workflow automation with AI agent nodes and Ollama integration |
| [Dify](dify.md) | AI application platform with RAG, agents, and visual workflows |

## See Also

- [Agent Frameworks](../agent-frameworks/index.md) -- code-based AI agent tools
- [Ollama](../inference-engines/ollama.md) -- local LLM inference engine
- [Open WebUI](../gui-tools/open-webui.md) -- chat interface for local models
- [Vector Databases](../vector-databases/index.md) -- storage for RAG embeddings
