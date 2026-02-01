# RAG Integration

Connecting RAG pipelines to applications, chat interfaces, and workflows.

## Chat Interface Integration

### Streamlit Chat App

```python
# app.py
import streamlit as st
from rag_pipeline import RAGChain, VectorStore

st.title("Document Q&A")

# Initialize RAG
@st.cache_resource
def get_rag():
    vectorstore = VectorStore(
        persist_directory="./data/vectordb",
        collection_name="documents",
    )
    return RAGChain(vectorstore=vectorstore)

rag = get_rag()

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about your documents"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            result = rag.query_with_sources(prompt)

        st.markdown(result["answer"])

        with st.expander("Sources"):
            for source in result["sources"]:
                st.markdown(f"- {source['metadata'].get('source', 'Unknown')}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"]
    })
```

### Gradio Interface

```python
import gradio as gr
from rag_pipeline import RAGChain, VectorStore

vectorstore = VectorStore(
    persist_directory="./data/vectordb",
    collection_name="documents",
)
rag = RAGChain(vectorstore=vectorstore)

def query_rag(question: str, history: list) -> str:
    result = rag.query_with_sources(question)

    answer = result["answer"]
    sources = "\n".join([
        f"- {s['metadata'].get('source', 'Unknown')}"
        for s in result["sources"]
    ])

    return f"{answer}\n\n**Sources:**\n{sources}"

demo = gr.ChatInterface(
    fn=query_rag,
    title="Document Q&A",
    description="Ask questions about your documents",
    examples=["What are the main topics?", "Summarize the key points"],
)

demo.launch()
```

## OpenAI-Compatible API

Wrap RAG as an OpenAI-compatible endpoint:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uuid
import time

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[dict]
    usage: dict

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    # Extract the last user message
    user_message = next(
        (m.content for m in reversed(request.messages) if m.role == "user"),
        ""
    )

    # Query RAG
    result = rag.query_with_sources(user_message)

    return ChatResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
        object="chat.completion",
        created=int(time.time()),
        model=request.model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result["answer"]
            },
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(result["answer"].split()),
            "total_tokens": len(user_message.split()) + len(result["answer"].split())
        }
    )
```

## MCP Server Integration

Create an MCP server for RAG:

```python
#!/usr/bin/env python3
"""RAG MCP Server"""
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
from rag_pipeline import RAGChain, VectorStore

server = Server("rag-server")

# Initialize RAG
vectorstore = VectorStore(
    persist_directory="./data/vectordb",
    collection_name="documents",
)
rag = RAGChain(vectorstore=vectorstore)

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_documents",
            description="Search and answer questions from indexed documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to answer"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="search_documents",
            description="Search for relevant document chunks",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 4
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_documents":
        result = rag.query_with_sources(arguments["question"])
        return [TextContent(
            type="text",
            text=f"Answer: {result['answer']}\n\nSources: {[s['metadata'].get('source') for s in result['sources']]}"
        )]

    elif name == "search_documents":
        docs = vectorstore.search(
            arguments["query"],
            k=arguments.get("k", 4)
        )
        results = "\n\n---\n\n".join([
            f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content[:500]}..."
            for doc in docs
        ])
        return [TextContent(type="text", text=results)]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

## Webhook Integration

Trigger RAG queries from external events:

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

WEBHOOK_SECRET = "your-secret-key"

def verify_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.post("/webhook/slack")
async def slack_webhook(request: Request):
    """Handle Slack slash commands."""
    form = await request.form()

    question = form.get("text", "")
    if not question:
        return {"text": "Please provide a question"}

    result = rag.query_with_sources(question)

    return {
        "response_type": "in_channel",
        "text": result["answer"],
        "attachments": [{
            "text": f"Sources: {', '.join([s['metadata'].get('source', 'Unknown') for s in result['sources']])}"
        }]
    }

@app.post("/webhook/github")
async def github_webhook(request: Request):
    """Handle GitHub issue comments."""
    signature = request.headers.get("X-Hub-Signature-256", "")
    payload = await request.body()

    if not verify_signature(payload, signature):
        raise HTTPException(status_code=401)

    data = await request.json()

    if data.get("action") == "created" and "comment" in data:
        comment = data["comment"]["body"]

        if comment.startswith("/ask"):
            question = comment[4:].strip()
            result = rag.query(question)

            # Post response (implement GitHub API call)
            # post_github_comment(data["issue"]["number"], result)

    return {"status": "ok"}
```

## Batch Processing

Process multiple queries efficiently:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class BatchRAG:
    def __init__(self, rag_chain: RAGChain, max_workers: int = 4):
        self.rag = rag_chain
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def query_batch(self, questions: list[str]) -> list[dict]:
        """Process multiple questions concurrently."""
        loop = asyncio.get_event_loop()

        tasks = [
            loop.run_in_executor(
                self.executor,
                self.rag.query_with_sources,
                question
            )
            for question in questions
        ]

        return await asyncio.gather(*tasks)

    def query_batch_sync(self, questions: list[str]) -> list[dict]:
        """Synchronous batch processing."""
        return asyncio.run(self.query_batch(questions))

# Usage
batch_rag = BatchRAG(rag)
questions = [
    "What is the main topic?",
    "Who are the authors?",
    "What are the key findings?",
]
results = batch_rag.query_batch_sync(questions)
```

## Conversation Memory

Maintain context across queries:

```python
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class ConversationalRAG:
    def __init__(self, rag_chain: RAGChain, memory_window: int = 5):
        self.rag = rag_chain
        self.memory = ConversationBufferWindowMemory(
            k=memory_window,
            return_messages=True,
            memory_key="chat_history"
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant answering questions based on documents.
            Use the context provided to answer questions.
            If you don't know, say so."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """Context: {context}

            Question: {question}"""),
        ])

    def query(self, question: str) -> str:
        # Get context
        docs = self.rag.retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])

        # Get chat history
        history = self.memory.load_memory_variables({})["chat_history"]

        # Generate response
        messages = self.prompt.format_messages(
            chat_history=history,
            context=context,
            question=question
        )

        response = self.rag.llm.invoke(messages)

        # Save to memory
        self.memory.save_context(
            {"input": question},
            {"output": response}
        )

        return response

    def clear_memory(self):
        self.memory.clear()
```

## Scheduled Ingestion

Automatically update the knowledge base:

```python
import schedule
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DocumentHandler(FileSystemEventHandler):
    def __init__(self, vectorstore, loader, chunker):
        self.vectorstore = vectorstore
        self.loader = loader
        self.chunker = chunker

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix in [".pdf", ".md", ".txt"]:
            print(f"New document: {path}")
            self.ingest_file(path)

    def ingest_file(self, path: Path):
        docs = self.loader.load_file(path)
        chunks = self.chunker.chunk(docs)
        self.vectorstore.add_documents(chunks)
        print(f"Ingested {len(chunks)} chunks from {path.name}")

# File watcher
def start_watcher(documents_dir: Path):
    handler = DocumentHandler(vectorstore, loader, chunker)
    observer = Observer()
    observer.schedule(handler, str(documents_dir), recursive=True)
    observer.start()
    return observer

# Scheduled re-index
def full_reindex():
    print("Starting full reindex...")
    vectorstore.delete_collection()
    documents = loader.load_all()
    chunks = chunker.chunk(documents)
    vectorstore.add_documents(chunks)
    print(f"Reindexed {len(chunks)} chunks")

schedule.every().sunday.at("02:00").do(full_reindex)

# Run scheduler
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)
```

## See Also

- [Implementation Guide](implementation.md)
- [MCP Guide](../mcp/index.md)
- [API Serving](../api-serving/index.md)
