# CrewAI

CrewAI enables building multi-agent systems where specialized agents collaborate to accomplish complex tasks.

## Installation

```bash
pip install crewai crewai-tools
```

## Core Concepts

### Agents

Specialized personas with roles and goals:

```python
from crewai import Agent
from langchain_community.llms import Ollama

llm = Ollama(model="llama3.2")

researcher = Agent(
    role="Research Analyst",
    goal="Find accurate and relevant information",
    backstory="You are an expert researcher with years of experience.",
    llm=llm,
    verbose=True,
)
```

### Tasks

Specific assignments for agents:

```python
from crewai import Task

research_task = Task(
    description="Research the latest developments in AI agents",
    expected_output="A summary of 5 key developments with sources",
    agent=researcher,
)
```

### Crews

Teams of agents working together:

```python
from crewai import Crew

crew = Crew(
    agents=[researcher],
    tasks=[research_task],
    verbose=True,
)

result = crew.kickoff()
```

## Multi-Agent Crew

```python
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama

llm = Ollama(model="llama3.2")

# Define agents
researcher = Agent(
    role="Senior Research Analyst",
    goal="Uncover cutting-edge developments in AI",
    backstory="""You work at a leading tech think tank.
    Your expertise lies in identifying emerging trends.""",
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

writer = Agent(
    role="Tech Content Writer",
    goal="Create engaging content about AI developments",
    backstory="""You are a renowned content writer specializing
    in technology and AI topics.""",
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

editor = Agent(
    role="Content Editor",
    goal="Ensure content is accurate, clear, and engaging",
    backstory="""You are an experienced editor with an eye
    for detail and clarity.""",
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

# Define tasks
research_task = Task(
    description="""Research the latest AI agent frameworks.
    Focus on their capabilities, limitations, and use cases.
    Your final answer must be a detailed report.""",
    expected_output="Detailed research report with key findings",
    agent=researcher,
)

writing_task = Task(
    description="""Using the research findings, write a blog post
    about AI agent frameworks. Make it engaging and informative
    for a technical audience.""",
    expected_output="Blog post draft (500-800 words)",
    agent=writer,
    context=[research_task],  # Depends on research
)

editing_task = Task(
    description="""Review and edit the blog post for clarity,
    accuracy, and engagement. Provide the final polished version.""",
    expected_output="Final edited blog post",
    agent=editor,
    context=[writing_task],  # Depends on writing
)

# Create crew
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential,  # Tasks run in order
    verbose=True,
)

result = crew.kickoff()
print(result)
```

## Agent Configuration

### With Memory

```python
researcher = Agent(
    role="Research Analyst",
    goal="Find information",
    backstory="Expert researcher",
    llm=llm,
    memory=True,  # Remember previous interactions
    verbose=True,
)
```

### With Delegation

```python
manager = Agent(
    role="Project Manager",
    goal="Coordinate the team",
    backstory="Experienced manager",
    llm=llm,
    allow_delegation=True,  # Can delegate to other agents
    verbose=True,
)
```

### With Tools

```python
from crewai_tools import (
    SerperDevTool,
    WebsiteSearchTool,
    FileReadTool,
)

search_tool = SerperDevTool()
web_tool = WebsiteSearchTool()
file_tool = FileReadTool()

researcher = Agent(
    role="Research Analyst",
    goal="Find information",
    backstory="Expert researcher",
    llm=llm,
    tools=[search_tool, web_tool, file_tool],
    verbose=True,
)
```

## Custom Tools

```python
from crewai_tools import BaseTool

class CalculatorTool(BaseTool):
    name: str = "Calculator"
    description: str = "Useful for mathematical calculations"

    def _run(self, expression: str) -> str:
        try:
            return str(eval(expression))
        except Exception as e:
            return f"Error: {e}"

calculator = CalculatorTool()

analyst = Agent(
    role="Data Analyst",
    goal="Analyze numerical data",
    backstory="Expert in data analysis",
    llm=llm,
    tools=[calculator],
)
```

## Process Types

### Sequential

Tasks run one after another:

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
)
```

### Hierarchical

Manager coordinates agents:

```python
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.hierarchical,
    manager_llm=llm,
)
```

## Task Configuration

### With Context

```python
writing_task = Task(
    description="Write based on research",
    expected_output="Blog post",
    agent=writer,
    context=[research_task],  # Has access to research results
)
```

### With Output File

```python
writing_task = Task(
    description="Write a report",
    expected_output="Detailed report",
    agent=writer,
    output_file="report.md",  # Save to file
)
```

### With Callback

```python
def task_callback(output):
    print(f"Task completed: {output}")

writing_task = Task(
    description="Write a report",
    expected_output="Report",
    agent=writer,
    callback=task_callback,
)
```

## Async Execution

```python
import asyncio

async def run_crew():
    result = await crew.kickoff_async()
    return result

result = asyncio.run(run_crew())
```

## Input Variables

```python
# Define task with variables
research_task = Task(
    description="Research {topic} and provide insights on {aspect}",
    expected_output="Research report",
    agent=researcher,
)

# Provide inputs at runtime
result = crew.kickoff(inputs={
    "topic": "AI agents",
    "aspect": "practical applications"
})
```

## Example: Code Review Crew

```python
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama

llm = Ollama(model="llama3.2")

# Agents
code_reviewer = Agent(
    role="Senior Code Reviewer",
    goal="Identify bugs, security issues, and improvements",
    backstory="20 years of software development experience",
    llm=llm,
)

security_analyst = Agent(
    role="Security Analyst",
    goal="Find security vulnerabilities",
    backstory="Cybersecurity expert specializing in code audits",
    llm=llm,
)

# Tasks
review_task = Task(
    description="""Review this code for bugs and improvements:

```python
{code}
```

Provide specific, actionable feedback.""",
    expected_output="Code review with specific issues and fixes",
    agent=code_reviewer,
)

security_task = Task(
    description="""Analyze the code for security vulnerabilities:

```python
{code}
```

Focus on OWASP top 10 vulnerabilities.""",
    expected_output="Security analysis with severity ratings",
    agent=security_analyst,
)

# Crew
review_crew = Crew(
    agents=[code_reviewer, security_analyst],
    tasks=[review_task, security_task],
    process=Process.sequential,
)

# Run
code = """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return db.execute(query)
"""

result = review_crew.kickoff(inputs={"code": code})
```

## See Also

- [Agent Frameworks Overview](index.md)
- [LangChain Guide](langchain.md)
- [Tools Guide](tools.md)
