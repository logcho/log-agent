# LangGraph ReAct Agent

A simple, educational, and robust implementation of a ReAct (Reasoning and Action) agent built using **LangGraph** and **LangChain**.

The agent has access to a comprehensive set of filesystem, subprocess, and GUI automation tools using Python's standard library and `pyautogui`. It uses a state graph to iterate between reasoning (calling the model) and acting (calling the tools) until it achieves the final answer.

## Features

- **LangGraph State Orchestration**: Implements a cyclic graph with state validation and edge routing.
- **Exposed OS Toolset**: Exposes operations for listing directories, reading/writing files, creating/deleting directories, finding matching files, moving/renaming, and inspecting file metadata.
- **System Command Execution & Application Opening**: Allows execution of terminal commands and opening of applications/files via `subprocess` returning output or errors safely.
- **GUI Automation (PyAutoGUI)**: Allows mouse movement, clicking, typing, hotkey combinations, and taking screenshots.
- **Rich Terminal UI**: Displays a colored CLI interface rendering agent nodes, thought processes, tool parameters, and results in a structured format.

## File Structure

- [agent.py](file:///Users/loganchoi/Desktop/os-tools/agent.py) - Contains the state definition, LLM binding, nodes, conditional edges, and graph compilation.
- [os_tools.py](file:///Users/loganchoi/Desktop/os-tools/os_tools.py) - Exposes various standard library filesystem operations via `@tool`.
- [system_tools.py](file:///Users/loganchoi/Desktop/os-tools/system_tools.py) - Exposes subprocess execution, application opening, and PyAutoGUI screen control via `@tool`.
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

1. **Information gathering:**
   > `What is the current directory and what are its contents?`
2. **Sequential file operations:**
   > `Create a directory named 'temp_testing', write a file 'notes.txt' inside it with the text 'hello world', and then read its contents back.`
3. **Searching and metadata:**
   > `Find all python files in this project and print the metadata (size, mod time) of agent.py.`
4. **Command Execution (subprocess):**
   > `Check the git status by running a terminal command.`
5. **Application Opening:**
   > `Open Safari on my computer.`
6. **GUI Automation (PyAutoGUI):**
   > `What is my screen size and current mouse position?`
7. **Compound Tasks:**
   > `Take a screenshot, save it as screenshot.png, and list all files in this directory to verify it is there.`
8. **Cleanup:**
   > `Remove the 'temp_testing' directory and all of its contents recursively.`
