import os
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Load environment variables from .env file
load_dotenv()

# =====================================================================
# 1. Define Agent State
# =====================================================================
class AgentState(TypedDict):
    """The state of our ReAct agent graph.
    
    It keeps track of the sequence of messages exchanged between the user, 
    the model, and the tools. The `add_messages` function specifies that 
    new messages should be appended to the existing list rather than overwriting.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]


# =====================================================================
# 2. Define Tools
# =====================================================================
from os_tools import os_toolset
from system_tools import system_toolset
from obsidian_tools import obsidian_toolset

# List of all tools available to the agent
tools = os_toolset + system_toolset + obsidian_toolset
tool_node = ToolNode(tools)


# =====================================================================
# 3. Define LLM & Bind Tools
# =====================================================================
def get_llm():
    """Initializes the chat model and binds the defined tools.
    
    Checks for the OPENAI_API_KEY environment variable. If not found,
    raises a clean ValueError to guide the user.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment. "
            "Please create a `.env` file from `.env.example` and set your key."
        )
    
    # Initialize OpenAI Chat Model (using gpt-4o-mini as a fast, cheap default)
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )
    
    # Bind the tools so the LLM is aware of them and can choose to invoke them
    return model.bind_tools(tools)


# =====================================================================
# 4. Define Nodes and Conditional Edges
# =====================================================================
def call_model(state: AgentState):
    """The node representing the agent's thought process.
    
    It invokes the LLM with the current list of messages and appends the 
    resulting assistant message to the state.
    """
    messages = state["messages"]
    model = get_llm()
    response = model.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """A conditional edge function that decides the next step.
    
    If the last message from the LLM contains tool calls, we route to the 'tools' node.
    Otherwise, we stop and transition to the END state.
    """
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


# =====================================================================
# 5. Build and Compile the Graph
# =====================================================================
# Initialize a StateGraph with the AgentState type
workflow = StateGraph(AgentState)

# Add nodes to the graph
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set the entrypoint (where execution starts)
workflow.add_edge(START, "agent")

# Add the conditional edge from the agent node
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# After tools are executed, we return to the agent node to evaluate the tool results
workflow.add_edge("tools", "agent")

# Compile the workflow into a runnable LangGraph application
agent_app = workflow.compile()
