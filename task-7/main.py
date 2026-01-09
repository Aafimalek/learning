"""
Multi-Agent Routing System - Main Entry Point

Usage:
    python main.py                    # Interactive mode
    python main.py "your query"       # Single query mode
    python main.py --analytics        # Show analytics

Architecture:
    User Query → Intent Classifier → Routing Policy → Specialized Agent → Output
"""

import sys
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Load environment variables
load_dotenv()

from graph import run_query, compile_graph
from logger import (
    print_full_state,
    print_logs_summary,
    print_analytics,
    append_log,
    console
)


# ============================================================================
# Interactive Mode
# ============================================================================

def interactive_mode():
    """Run the system in interactive mode."""
    console.print(Panel.fit(
        "[bold blue]🤖 Multi-Agent Routing System[/bold blue]\n\n"
        "Routes your queries to specialized agents:\n"
        "• 📝 Blog Agent - Long-form writing\n"
        "• 💻 Code Agent - Code generation\n"
        "• ❓ QNA Agent - Quick answers\n"
        "• 🔬 Research Agent - In-depth analysis\n"
        "• 🤔 Clarify Agent - Ambiguous queries\n\n"
        "Commands: 'quit', 'logs', 'analytics', 'debug'",
        border_style="blue"
    ))
    
    debug_mode = False
    
    while True:
        try:
            query = Prompt.ask("\n[bold green]You[/bold green]")
            
            if not query.strip():
                continue
            
            # Special commands
            if query.lower() == 'quit':
                console.print("[dim]Goodbye![/dim]")
                break
            
            if query.lower() == 'logs':
                # Show recent logs
                console.print("\n[bold]Recent Logs:[/bold]")
                print_analytics(1)
                continue
            
            if query.lower() == 'analytics':
                print_analytics(7)
                continue
            
            if query.lower() == 'debug':
                debug_mode = not debug_mode
                console.print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
                continue
            
            # Process query
            console.print("\n[dim]Processing...[/dim]")
            
            result = run_query(query)
            
            # Log the result
            append_log(result)
            
            # Display results
            if debug_mode:
                print_full_state(result)
                print_logs_summary(result)
            else:
                # Just show the output
                response = result.get("agent_response")
                if response and response.raw_output:
                    # Show which agent handled it
                    classification = result.get("classification")
                    if classification:
                        console.print(f"\n[dim]Intent: {classification.intent.value} (conf: {classification.confidence:.0%})[/dim]")
                    
                    console.print(Panel(
                        response.raw_output,
                        title=f"[bold]{result.get('routed_to', 'Agent')}[/bold]",
                        border_style="green"
                    ))
                elif response and response.error:
                    console.print(f"[red]Error: {response.error}[/red]")
                else:
                    console.print("[yellow]No response generated[/yellow]")
                    
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type 'quit' to exit.[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# Single Query Mode
# ============================================================================

def single_query_mode(query: str):
    """Process a single query and exit."""
    console.print(f"\n[bold]Query:[/bold] {query}")
    
    result = run_query(query)
    
    # Log the result
    append_log(result)
    
    # Display full results
    print_full_state(result)


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        console.print("[red]Error: GROQ_API_KEY not found in environment[/red]")
        console.print("Please set GROQ_API_KEY in your .env file")
        sys.exit(1)
    
    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--analytics":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            print_analytics(days)
        elif arg == "--help":
            console.print("""
[bold]Multi-Agent Routing System[/bold]

Usage:
    python main.py                    Interactive mode
    python main.py "query"            Single query mode
    python main.py --analytics [N]    Show analytics for N days (default: 7)
    python main.py --help             Show this help
            """)
        else:
            # Treat as query
            single_query_mode(arg)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
