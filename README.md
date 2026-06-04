# LangGraph ReAct Agent

A simple, educational, and robust implementation of a ReAct (Reasoning and Action) agent built using **LangGraph** and **LangChain**.

The agent has access to basic math tools (addition and multiplication) and uses a state graph to iterate between reasoning (calling the model) and acting (calling the tools) until it achieves the final answer.

## Features

- **LangGraph State Orchestration**: Implements a cyclic graph with state validation and edge routing.
- **Custom Tool Integration**: Registers custom Python functions as tools decorated with LangChain `@tool`.
- **Rich Terminal UI**: Displays a colored CLI interface rendering agent nodes, thought processes, tool parameters, and results in a structured format.

## File Structure

- [agent.py](file:///Users/loganchoi/Desktop/os-tools/agent.py) - Contains the state definition, arithmetic tools, LLM binding, nodes, conditional edges, and graph compilation.
- [main.py](file:///Users/loganchoi/Desktop/os-tools/main.py) - Contains the interactive CLI REPL and visualization using `rich`.
- [requirements.txt](file:///Users/loganchoi/Desktop/os-tools/requirements.txt) - List of python dependencies.
- [.env.example](file:///Users/loganchoi/Desktop/os-tools/.env.example) - Template for setting environment variables.

## Getting Started

### 1. Prerequisites

Make sure you have Python 3.9+ installed.

### 2. Setup Environment

Create a virtual environment, activate it, and install dependencies:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key

Copy `.env.example` to `.env` and fill in your OpenAI API Key:

```bash
cp .env.example .env
```

Open `.env` in your editor and configure:
```env
OPENAI_API_KEY=sk-...
```

### 4. Run the Agent

Execute the interactive command line utility:

```bash
python3 main.py
```

### Example Queries to Try

1. **Simple math needing tool execution:**
   > `What is 382 multiplied by 43?`
2. **Compound math needing multiple sequential tool executions:**
   > `What is 35 multiplied by 12, and then add 145 to the result?`
3. **General knowledge (not requiring tools):**
   > `Explain what a neural network is in one sentence.`
