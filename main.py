import sys
import os
from dotenv import load_dotenv

# Ensure the current directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent import agent_app

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme
from rich.text import Text
from rich.markdown import Markdown

# Custom styling for a premium terminal appearance
custom_theme = Theme({
    "agent.banner": "bold bright_magenta",
    "agent.node": "bold cyan",
    "agent.tool": "bold yellow",
    "agent.final": "bold green",
    "agent.error": "bold red",
    "user.prompt": "bold green",
    "border.agent": "cyan",
    "border.tool": "yellow",
    "border.final": "green"
})

console = Console(theme=custom_theme)

def print_welcome_banner():
    """Prints a premium welcome banner using rich."""
    banner_text = Text()
    banner_text.append("🧠 LangGraph ReAct Agent CLI\n", style="agent.banner")
    banner_text.append("───────────────────────────────\n", style="dim white")
    banner_text.append("Type your question below. The agent can use these tools:\n", style="italic white")
    banner_text.append("• add(a, b) -> a + b\n", style="bold yellow")
    banner_text.append("• multiply(a, b) -> a * b\n", style="bold yellow")
    banner_text.append("───────────────────────────────\n", style="dim white")
    banner_text.append("Type 'exit', 'quit', or press Ctrl+C to end the session.", style="dim red")
    
    console.print(Panel(banner_text, border_style="bright_magenta", expand=False))

def run_agent(query: str):
    """Executes the LangGraph agent workflow and streams intermediate steps."""
    console.print(f"\n[info]🚀 Starting agent workflow...[/info]")
    
    # Initialize the messages state
    initial_state = {
        "messages": [HumanMessage(content=query)]
    }
    
    try:
        # stream_mode="updates" yields updates from each node after it executes
        for chunk in agent_app.stream(initial_state, stream_mode="updates"):
            for node_name, state_update in chunk.items():
                console.print(f"\n[agent.node]📍 Node Executed: {node_name.upper()}[/agent.node]")
                
                # Check messages added by this node
                messages = state_update.get("messages", [])
                for msg in messages:
                    if isinstance(msg, AIMessage):
                        # Show thoughts/text output from agent
                        if msg.content:
                            # Render agent markdown thoughts in a panel
                            console.print(Panel(
                                Markdown(msg.content),
                                title="🤖 Agent Thought",
                                border_style="border.agent"
                            ))
                        
                        # Show if agent requested tool execution
                        if msg.tool_calls:
                            for tc in msg.tool_calls:
                                tool_info = f"🔨 Tool Call: [bold]{tc['name']}[/bold]\nArguments: [dim]{tc['args']}[/dim]"
                                console.print(Panel(
                                    tool_info,
                                    title="🔧 Tool Call Request",
                                    border_style="border.tool"
                                ))
                                
                    elif isinstance(msg, ToolMessage):
                        # Show tool execution results
                        tool_result = f"Output: [bold]{msg.content}[/bold]"
                        console.print(Panel(
                            tool_result,
                            title=f"📥 Tool Output ({msg.name})",
                            border_style="border.tool"
                        ))
                        
    except Exception as e:
        console.print(f"\n[agent.error]❌ Error running agent: {str(e)}[/agent.error]\n")

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for API Key before starting the CLI loop
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print(Panel(
            "[bold red]Error: OPENAI_API_KEY not found in environment.[/bold red]\n\n"
            "Please do the following:\n"
            "1. Copy [bold].env.example[/bold] to [bold].env[/bold]:\n"
            "   [dim]cp .env.example .env[/dim]\n"
            "2. Open [bold].env[/bold] and add your OpenAI API Key:\n"
            "   [dim]OPENAI_API_KEY=sk-...[/dim]\n"
            "3. Restart this application.",
            title="⚠️ Missing Configuration",
            border_style="red"
        ))
        sys.exit(1)
        
    print_welcome_banner()
    
    while True:
        try:
            # Prompt user for input
            user_input = Prompt.ask("\n[user.prompt]Query[/user.prompt]")
            
            # Check exit commands
            if user_input.strip().lower() in ["exit", "quit"]:
                console.print("\n[agent.banner]Goodbye! 👋[/agent.banner]")
                break
                
            if not user_input.strip():
                continue
                
            run_agent(user_input)
            
        except KeyboardInterrupt:
            console.print("\n\n[agent.banner]Goodbye! 👋[/agent.banner]")
            break
        except Exception as e:
            console.print(f"\n[agent.error]An unexpected error occurred: {e}[/agent.error]")

if __name__ == "__main__":
    main()
