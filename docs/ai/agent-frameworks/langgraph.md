# LangGraph

LangGraph is LangChain's framework for building stateful, multi-step agent workflows as graphs.

## Installation

```bash
pip install langgraph langchain langchain-community
```

## Why LangGraph?

- **Explicit control flow** - Define exactly how agents behave
- **State management** - Track information across steps
- **Cycles and branches** - Complex decision trees
- **Human-in-the-loop** - Pause for approval
- **Persistence** - Save and resume workflows

## Core Concepts

### Graph Structure

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  START  │────>│  Node   │────>│   END   │
└─────────┘     └─────────┘     └─────────┘
                    │
                    v
               ┌─────────┐
               │  Node   │
               └─────────┘
```

### State

State flows through the graph:

```python
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add]  # Append messages
    next_step: str
```

## Basic Graph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Define state
class State(TypedDict):
    input: str
    output: str

# Define nodes (functions)
def process(state: State) -> State:
    return {"output": state["input"].upper()}

# Build graph
graph = StateGraph(State)

# Add nodes
graph.add_node("process", process)

# Add edges
graph.set_entry_point("process")
graph.add_edge("process", END)

# Compile
app = graph.compile()

# Run
result = app.invoke({"input": "hello"})
print(result["output"])  # HELLO
```

## Conditional Routing

```python
from langgraph.graph import StateGraph, END

class State(TypedDict):
    input: str
    classification: str
    output: str

def classify(state: State) -> State:
    # Classify the input
    if "help" in state["input"].lower():
        return {"classification": "support"}
    else:
        return {"classification": "general"}

def handle_support(state: State) -> State:
    return {"output": "Routing to support team..."}

def handle_general(state: State) -> State:
    return {"output": "General response..."}

def route(state: State) -> str:
    """Decide next node based on state."""
    if state["classification"] == "support":
        return "support"
    return "general"

# Build graph
graph = StateGraph(State)

graph.add_node("classify", classify)
graph.add_node("support", handle_support)
graph.add_node("general", handle_general)

graph.set_entry_point("classify")

# Conditional edge
graph.add_conditional_edges(
    "classify",
    route,
    {
        "support": "support",
        "general": "general"
    }
)

graph.add_edge("support", END)
graph.add_edge("general", END)

app = graph.compile()
```

## Agent with Tools

```python
from langchain_community.llms import Ollama
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# LLM
llm = Ollama(model="llama3.2")

# Tools
@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool
def calculate(expression: str) -> str:
    """Calculate math expression."""
    return str(eval(expression))

tools = [search, calculate]

# State
class AgentState(TypedDict):
    messages: list
    tool_calls: list

# Nodes
def agent(state: AgentState) -> AgentState:
    """LLM decides what to do."""
    messages = state["messages"]
    response = llm.invoke(str(messages))

    # Parse for tool calls (simplified)
    if "TOOL:" in response:
        tool_name = response.split("TOOL:")[1].split()[0]
        tool_input = response.split("INPUT:")[1].strip()
        return {"tool_calls": [{"name": tool_name, "input": tool_input}]}

    return {"messages": [response], "tool_calls": []}

def should_continue(state: AgentState) -> str:
    """Decide if we should use tools or end."""
    if state.get("tool_calls"):
        return "tools"
    return "end"

# Build graph
graph = StateGraph(AgentState)

graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

graph.add_edge("tools", "agent")  # Loop back

app = graph.compile()
```

## Prebuilt Agents

### ReAct Agent

```python
from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model="llama3.2")

agent = create_react_agent(llm, tools)

result = agent.invoke({"messages": [("human", "Search for Python tutorials")]})
```

## Human-in-the-Loop

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

class State(TypedDict):
    input: str
    approved: bool
    output: str

def process(state: State) -> State:
    return {"output": f"Processed: {state['input']}"}

def check_approval(state: State) -> str:
    if state.get("approved"):
        return "process"
    return "wait"

graph = StateGraph(State)
graph.add_node("process", process)

graph.set_entry_point("check_approval")
graph.add_conditional_edges(
    "check_approval",
    check_approval,
    {"process": "process", "wait": END}
)
graph.add_edge("process", END)

# Add checkpointing
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# First run - waits for approval
config = {"configurable": {"thread_id": "1"}}
result = app.invoke({"input": "Important task", "approved": False}, config)

# Later - approve and continue
result = app.invoke({"input": "Important task", "approved": True}, config)
```

## Persistence

### Memory Checkpointer

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# Each thread has separate state
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke({"input": "Hello"}, config)

# Resume later
result = app.invoke({"input": "Continue"}, config)
```

### SQLite Checkpointer

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("./checkpoints.db")
app = graph.compile(checkpointer=checkpointer)
```

## Streaming

```python
# Stream events
for event in app.stream({"input": "Hello"}):
    print(event)

# Stream specific events
for event in app.stream({"input": "Hello"}, stream_mode="updates"):
    print(event)
```

## Subgraphs

```python
# Create a subgraph
subgraph = StateGraph(SubState)
# ... define subgraph ...
compiled_subgraph = subgraph.compile()

# Use in main graph
main_graph = StateGraph(MainState)
main_graph.add_node("subprocess", compiled_subgraph)
```

## Multi-Agent Pattern

```python
class MultiAgentState(TypedDict):
    messages: list
    current_agent: str
    task_complete: bool

def researcher(state: MultiAgentState) -> MultiAgentState:
    """Research agent."""
    # Do research
    return {"messages": state["messages"] + ["Research complete"]}

def writer(state: MultiAgentState) -> MultiAgentState:
    """Writer agent."""
    # Write content
    return {"messages": state["messages"] + ["Writing complete"]}

def supervisor(state: MultiAgentState) -> str:
    """Decide which agent to use next."""
    if "Research complete" not in state["messages"]:
        return "researcher"
    elif "Writing complete" not in state["messages"]:
        return "writer"
    return "end"

graph = StateGraph(MultiAgentState)

graph.add_node("researcher", researcher)
graph.add_node("writer", writer)

graph.set_entry_point("supervisor")
graph.add_conditional_edges(
    "supervisor",
    supervisor,
    {
        "researcher": "researcher",
        "writer": "writer",
        "end": END
    }
)

graph.add_edge("researcher", "supervisor")
graph.add_edge("writer", "supervisor")

app = graph.compile()
```

## Visualization

```python
# Generate Mermaid diagram
print(app.get_graph().draw_mermaid())

# Or save as PNG (requires graphviz)
app.get_graph().draw_png("graph.png")
```

## See Also

- [LangChain Guide](langchain.md)
- [Agent Frameworks Overview](index.md)
- [Tools Guide](tools.md)
