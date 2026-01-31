# LangChain

LangChain is the most popular framework for building LLM applications, including agents, RAG pipelines, and chains.

## Installation

```bash
pip install langchain langchain-community langchain-core
```

## Core Concepts

### LLMs and Chat Models

```python
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama

# Completion model
llm = Ollama(model="llama3.2", base_url="http://localhost:11434")
response = llm.invoke("What is Python?")

# Chat model
chat = ChatOllama(model="llama3.2")
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is Python?")
]
response = chat.invoke(messages)
```

### Prompts

```python
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# Simple prompt
prompt = PromptTemplate.from_template("Tell me about {topic}")
formatted = prompt.format(topic="Python")

# Chat prompt
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}")
])
messages = chat_prompt.format_messages(question="What is Python?")
```

### Chains (LCEL)

LangChain Expression Language for composing components:

```python
from langchain_core.output_parsers import StrOutputParser

# Simple chain
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"topic": "Python"})

# With chat model
chat_chain = chat_prompt | chat | StrOutputParser()
result = chat_chain.invoke({"question": "What is Python?"})
```

## Agents

### Basic Agent

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain.tools import Tool

# Define tools
tools = [
    Tool(
        name="calculator",
        func=lambda x: str(eval(x)),
        description="Calculate mathematical expressions"
    )
]

# Agent prompt
prompt = PromptTemplate.from_template("""
Answer the question using the available tools.

Tools: {tools}
Tool Names: {tool_names}

Question: {input}
{agent_scratchpad}
""")

# Create agent
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Run
result = executor.invoke({"input": "What is 25 * 4?"})
```

### Tool Calling Agent

For models with native tool support:

```python
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(chat, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
```

### Structured Output Agent

```python
from langchain.agents import create_structured_chat_agent

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant. Respond with a JSON object.

Available tools:
{tools}

To use a tool, respond with:
```json
{{"action": "tool_name", "action_input": "input"}}
```

When done:
```json
{{"action": "Final Answer", "action_input": "your response"}}
```"""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_structured_chat_agent(llm, tools, prompt)
```

## Custom Tools

### Function Tools

```python
from langchain.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implementation
    return "Search results..."

@tool
def read_file(path: str) -> str:
    """Read a file from disk."""
    with open(path) as f:
        return f.read()

@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    with open(path, 'w') as f:
        f.write(content)
    return f"Written to {path}"
```

### Class-Based Tools

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class CalculatorInput(BaseModel):
    expression: str = Field(description="Mathematical expression to evaluate")

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate mathematical expressions"
    args_schema = CalculatorInput

    def _run(self, expression: str) -> str:
        try:
            return str(eval(expression))
        except Exception as e:
            return f"Error: {e}"

    async def _arun(self, expression: str) -> str:
        return self._run(expression)
```

### Toolkit

```python
from langchain.agents import load_tools

# Built-in tools
tools = load_tools(["llm-math", "wikipedia"], llm=llm)

# File system toolkit
from langchain_community.agent_toolkits import FileManagementToolkit

toolkit = FileManagementToolkit(root_dir="./workspace")
tools = toolkit.get_tools()
```

## RAG with LangChain

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load and split documents
from langchain_community.document_loaders import DirectoryLoader

loader = DirectoryLoader("./docs", glob="**/*.md")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# Create vectorstore
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(chunks, embeddings)

# Create RAG chain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
)

# Query
result = qa.invoke("What is the main topic?")
```

## Memory

### Conversation Buffer

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

memory = ConversationBufferMemory()

chain = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

chain.invoke({"input": "Hi, I'm Alice"})
chain.invoke({"input": "What's my name?"})  # Remembers Alice
```

### Conversation Summary

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(llm=llm)
```

### Window Memory

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(k=5)  # Keep last 5 exchanges
```

## Callbacks

### Streaming

```python
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

llm = Ollama(
    model="llama3.2",
    callbacks=[StreamingStdOutCallbackHandler()]
)
```

### Custom Callback

```python
from langchain.callbacks.base import BaseCallbackHandler

class MyCallback(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"Starting LLM with: {prompts[0][:50]}...")

    def on_llm_end(self, response, **kwargs):
        print(f"LLM finished")

    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"Using tool: {serialized['name']}")

llm = Ollama(model="llama3.2", callbacks=[MyCallback()])
```

## Output Parsers

### String Parser

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | llm | StrOutputParser()
```

### JSON Parser

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

class Response(BaseModel):
    answer: str
    confidence: float

parser = JsonOutputParser(pydantic_object=Response)

prompt = PromptTemplate(
    template="Answer the question.\n{format_instructions}\nQuestion: {question}",
    input_variables=["question"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

chain = prompt | llm | parser
result = chain.invoke({"question": "What is 2+2?"})
# {"answer": "4", "confidence": 1.0}
```

### Structured Output

```python
from langchain_core.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=Response)
```

## Async Operations

```python
import asyncio

async def async_chain():
    # Async invoke
    result = await chain.ainvoke({"input": "Hello"})

    # Async stream
    async for chunk in chain.astream({"input": "Hello"}):
        print(chunk, end="")

    # Async batch
    results = await chain.abatch([
        {"input": "Hello"},
        {"input": "World"}
    ])

asyncio.run(async_chain())
```

## LangSmith Integration

For debugging and monitoring:

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "my-project"

# All chains are now traced
```

## See Also

- [LangGraph](langgraph.md)
- [Agent Frameworks Overview](index.md)
- [RAG Implementation](../rag/index.md)
- [Tools Guide](tools.md)
