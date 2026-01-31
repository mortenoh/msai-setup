# Agent Frameworks

Agent frameworks enable LLMs to reason, plan, use tools, and accomplish complex tasks autonomously.

## What Are AI Agents?

Agents go beyond simple question-answering by:

- **Reasoning** about how to solve problems
- **Planning** multi-step approaches
- **Using tools** to interact with the world
- **Iterating** based on results

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Loop                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   User Input                                                │
│       │                                                     │
│       v                                                     │
│   ┌───────────┐                                             │
│   │  Reason   │ ←─────────────────────────┐                 │
│   │  (LLM)    │                           │                 │
│   └───────────┘                           │                 │
│       │                                   │                 │
│       v                                   │                 │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐          │
│   │   Plan    │───>│   Act     │───>│  Observe  │          │
│   │           │    │  (Tools)  │    │  (Result) │──────────┘
│   └───────────┘    └───────────┘    └───────────┘          │
│                                           │                 │
│                                           v                 │
│                                      Final Output           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Framework Comparison

| Framework | Best For | Complexity | Local LLM Support |
|-----------|----------|------------|-------------------|
| LangChain | General agents, RAG | Medium | Good |
| LangGraph | Complex workflows | High | Good |
| CrewAI | Multi-agent teams | Medium | Good |
| AutoGen | Research, coding | High | Limited |
| Smolagents | Simple agents | Low | Good |

## In This Section

| Document | Description |
|----------|-------------|
| [LangChain](langchain.md) | Most popular framework |
| [LangGraph](langgraph.md) | Stateful agent workflows |
| [CrewAI](crewai.md) | Multi-agent collaboration |
| [Tools](tools.md) | Building custom tools |

## Quick Start: Simple Agent

### LangChain Agent

```python
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
import subprocess

# Local LLM
llm = Ollama(model="llama3.2")

# Define a tool
def run_shell(command: str) -> str:
    """Run a shell command and return output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout or result.stderr

tools = [
    Tool(
        name="shell",
        func=run_shell,
        description="Run shell commands. Input should be a valid shell command."
    )
]

# Create agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

# Run
agent.invoke("What files are in the current directory?")
```

### CrewAI Agent

```python
from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama

llm = Ollama(model="llama3.2")

# Define agent
researcher = Agent(
    role="Research Analyst",
    goal="Find and analyze information",
    backstory="You are an expert at finding information.",
    llm=llm,
    verbose=True,
)

# Define task
task = Task(
    description="Research the latest developments in AI agents",
    expected_output="A summary of key developments",
    agent=researcher,
)

# Run
crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

## Tool Types

### Built-in Tools

```python
from langchain_community.tools import (
    DuckDuckGoSearchRun,
    WikipediaQueryRun,
    ShellTool,
)
from langchain_community.utilities import WikipediaAPIWrapper

tools = [
    DuckDuckGoSearchRun(),
    WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
    ShellTool(),
]
```

### Custom Tools

```python
from langchain.tools import tool

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

@tool
def read_file(path: str) -> str:
    """Read contents of a file."""
    with open(path) as f:
        return f.read()
```

### MCP Tools

```python
# Use MCP servers as tools
# See docs/ai/mcp/index.md for details
```

## Agent Patterns

### ReAct (Reasoning + Acting)

The most common pattern:

1. **Thought**: Reason about the task
2. **Action**: Choose a tool
3. **Observation**: See the result
4. Repeat until done

### Plan-and-Execute

For complex tasks:

1. **Plan**: Break task into steps
2. **Execute**: Perform each step
3. **Replan**: Adjust based on results

### Multi-Agent

Multiple specialized agents:

```
User Query
    │
    v
┌─────────────┐
│  Manager    │ (coordinates)
└─────────────┘
    │
    ├──> Researcher (finds info)
    ├──> Analyst (processes data)
    └──> Writer (creates output)
```

## Local LLM Considerations

### Model Requirements

Agents need models that can:
- Follow instructions precisely
- Generate valid JSON/tool calls
- Reason in steps

**Recommended models:**
- Llama 3.2 (8B+)
- Qwen 2.5 (7B+)
- Mistral (7B+)

### Prompting for Local Models

Local models may need explicit prompting:

```python
from langchain_core.prompts import PromptTemplate

agent_prompt = PromptTemplate.from_template("""
You are a helpful assistant with access to tools.

Available tools:
{tools}

To use a tool, respond with:
Thought: [your reasoning]
Action: [tool name]
Action Input: [tool input]

When you have the final answer, respond with:
Thought: I now have the answer
Final Answer: [your response]

Question: {input}
{agent_scratchpad}
""")
```

## Error Handling

```python
from langchain.agents import AgentExecutor

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,           # Prevent infinite loops
    max_execution_time=60,       # Timeout
    handle_parsing_errors=True,  # Recover from bad outputs
    return_intermediate_steps=True,  # Debug info
)
```

## See Also

- [LangChain Guide](langchain.md)
- [MCP Protocol](../mcp/index.md)
- [Tools Guide](tools.md)
- [RAG Implementation](../rag/index.md)
