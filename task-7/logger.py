"""
Logging and Introspection Module.

Log every hop:
- User query
- Classified intent
- Confidence
- Chosen route
- Agent output length

Within a week, patterns will emerge:
- Misclassified queries
- Intents that overlap
- Missing agent types

This feeds back into intent design (Step 1).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from schemas import GraphState, LogEntry, IntentType


# ============================================================================
# Console Setup
# ============================================================================

console = Console()


# ============================================================================
# Log File Management
# ============================================================================

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def get_log_file() -> Path:
    """Get today's log file."""
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"routing_log_{today}.jsonl"


def append_log(state: GraphState) -> None:
    """Append logs from state to the log file."""
    log_file = get_log_file()
    
    logs = state.get("logs", [])
    query = state.get("user_query", "")
    
    # Create a summary entry
    summary = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "classification": None,
        "confidence": None,
        "routed_to": state.get("routed_to"),
        "success": False,
        "output_length": 0,
        "execution_logs": logs
    }
    
    if state.get("classification"):
        classification = state["classification"]
        summary["classification"] = classification.intent.value
        summary["confidence"] = classification.confidence
    
    if state.get("agent_response"):
        response = state["agent_response"]
        summary["success"] = response.success
        if response.raw_output:
            summary["output_length"] = len(response.raw_output)
    
    with open(log_file, "a") as f:
        f.write(json.dumps(summary) + "\n")


# ============================================================================
# Pretty Printing
# ============================================================================

def print_classification(state: GraphState) -> None:
    """Pretty print classification results."""
    classification = state.get("classification")
    
    if not classification:
        console.print("[red]No classification available[/red]")
        return
    
    # Confidence color coding
    confidence = classification.confidence
    if confidence >= 0.8:
        conf_color = "green"
    elif confidence >= 0.6:
        conf_color = "yellow"
    else:
        conf_color = "red"
    
    table = Table(title="🎯 Intent Classification", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    table.add_row("Intent", f"[bold]{classification.intent.value}[/bold]")
    table.add_row("Confidence", f"[{conf_color}]{confidence:.2%}[/{conf_color}]")
    table.add_row("Reasoning", classification.reasoning)
    
    console.print(table)


def print_routing(state: GraphState) -> None:
    """Pretty print routing decision."""
    routed_to = state.get("routed_to", "unknown")
    
    # Agent emoji map
    emoji_map = {
        "blog_agent": "📝",
        "code_agent": "💻",
        "qna_agent": "❓",
        "research_agent": "🔬",
        "clarify_agent": "🤔"
    }
    
    emoji = emoji_map.get(routed_to, "❓")
    console.print(f"\n{emoji} [bold]Routing to:[/bold] {routed_to}")


def print_response(state: GraphState) -> None:
    """Pretty print agent response."""
    response = state.get("agent_response")
    
    if not response:
        console.print("[red]No response available[/red]")
        return
    
    # Status indicator
    status = "✅ Success" if response.success else "❌ Failed"
    
    console.print(f"\n[bold]{status}[/bold]")
    
    if response.error:
        console.print(f"[red]Error: {response.error}[/red]")
        return
    
    if response.raw_output:
        # For code output, use syntax highlighting
        if response.agent_type == IntentType.CODE and "```" in response.raw_output:
            console.print(Panel(response.raw_output, title="Output", border_style="green"))
        else:
            # Truncate long outputs
            output = response.raw_output
            if len(output) > 1000:
                output = output[:1000] + "\n\n[dim]... (truncated)[/dim]"
            console.print(Panel(output, title="Output", border_style="green"))
    
    if response.execution_time_ms:
        console.print(f"[dim]Execution time: {response.execution_time_ms:.0f}ms[/dim]")


def print_full_state(state: GraphState) -> None:
    """Print the complete state for debugging."""
    print_classification(state)
    print_routing(state)
    print_response(state)


def print_logs_summary(state: GraphState) -> None:
    """Print a summary of all log entries."""
    logs = state.get("logs", [])
    
    if not logs:
        console.print("[dim]No logs recorded[/dim]")
        return
    
    table = Table(title="📋 Execution Log")
    table.add_column("Step", style="cyan")
    table.add_column("Intent")
    table.add_column("Confidence")
    table.add_column("Route")
    table.add_column("Output Len")
    table.add_column("Error", style="red")
    
    for log in logs:
        table.add_row(
            log.get("step", ""),
            log.get("classified_intent", ""),
            f"{log.get('confidence', 0):.2f}" if log.get("confidence") else "",
            log.get("chosen_route", ""),
            str(log.get("output_length", "")) if log.get("output_length") else "",
            log.get("error", "")[:30] if log.get("error") else ""
        )
    
    console.print(table)


# ============================================================================
# Analytics (for pattern detection)
# ============================================================================

def load_logs(days: int = 7) -> list[dict]:
    """Load logs from the past N days."""
    all_logs = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        log_file = LOG_DIR / f"routing_log_{date.strftime('%Y-%m-%d')}.jsonl"
        
        if log_file.exists():
            with open(log_file) as f:
                for line in f:
                    try:
                        all_logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    
    return all_logs


def analyze_logs(days: int = 7) -> dict:
    """Analyze logs for patterns."""
    from datetime import timedelta
    
    logs = load_logs(days)
    
    if not logs:
        return {"error": "No logs found"}
    
    # Basic stats
    total = len(logs)
    by_intent = {}
    by_route = {}
    low_confidence = []
    failures = []
    
    for log in logs:
        intent = log.get("classification")
        route = log.get("routed_to")
        confidence = log.get("confidence", 0)
        success = log.get("success", False)
        
        if intent:
            by_intent[intent] = by_intent.get(intent, 0) + 1
        if route:
            by_route[route] = by_route.get(route, 0) + 1
        
        if confidence and confidence < 0.6:
            low_confidence.append({
                "query": log.get("query"),
                "confidence": confidence,
                "intent": intent
            })
        
        if not success:
            failures.append({
                "query": log.get("query"),
                "route": route
            })
    
    return {
        "total_queries": total,
        "by_intent": by_intent,
        "by_route": by_route,
        "low_confidence_queries": low_confidence[:10],  # Top 10
        "failures": failures[:10],
        "success_rate": (total - len(failures)) / total if total > 0 else 0
    }


def print_analytics(days: int = 7) -> None:
    """Pretty print analytics."""
    from datetime import timedelta
    
    analytics = analyze_logs(days)
    
    if "error" in analytics:
        console.print(f"[red]{analytics['error']}[/red]")
        return
    
    console.print(f"\n[bold]📊 Analytics for past {days} days[/bold]\n")
    console.print(f"Total queries: {analytics['total_queries']}")
    console.print(f"Success rate: {analytics['success_rate']:.1%}")
    
    # Intent distribution
    if analytics["by_intent"]:
        table = Table(title="Intent Distribution")
        table.add_column("Intent")
        table.add_column("Count")
        table.add_column("Percentage")
        
        total = analytics["total_queries"]
        for intent, count in sorted(analytics["by_intent"].items(), key=lambda x: -x[1]):
            table.add_row(intent, str(count), f"{count/total:.1%}")
        
        console.print(table)
    
    # Low confidence queries (potential misclassifications)
    if analytics["low_confidence_queries"]:
        console.print("\n[yellow]⚠️ Low confidence queries (potential misclassifications):[/yellow]")
        for q in analytics["low_confidence_queries"][:5]:
            console.print(f"  • {q['query'][:50]}... (conf: {q['confidence']:.2f})")


# Add missing import
from datetime import timedelta
