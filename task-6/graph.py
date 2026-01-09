"""
LangGraph workflow for the research agent.
Defines the state machine and routing logic.
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from schemas import AgentState
from agents import (
    planner_node,
    search_node,
    reader_node,
    verification_node,
    synthesis_node,
    answer_node
)


# ============================================================================
# Routing Functions
# ============================================================================

def route_after_step(state: AgentState) -> Literal["continue", "error", "end"]:
    """
    Determine next action based on state.
    
    Routing logic:
    - if success → next step
    - if error → check retries → fallback → log → continue or end
    """
    if state.get("error_state"):
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)
        
        if retry_count < max_retries:
            return "continue"  # Retry current step
        return "error"  # Max retries exceeded
    
    if not state.get("should_continue", True):
        return "end"
    
    return "continue"


def get_next_step(state: AgentState) -> str:
    """Get the next step based on current_step."""
    current = state.get("current_step", "plan")
    
    step_order = {
        "plan": "search",
        "search": "read",
        "read": "verify",
        "verify": "synthesize",
        "synthesize": "answer",
        "answer": "complete",
        "complete": "complete"
    }
    
    return step_order.get(current, "complete")


# ============================================================================
# Error Handling Node
# ============================================================================

def error_handler_node(state: AgentState) -> dict:
    """
    Handle errors gracefully.
    Attempts to provide partial results or meaningful error message.
    """
    error = state.get("error_state", "Unknown error")
    current_step = state.get("current_step", "unknown")
    
    # Try to salvage what we have
    synthesis = state.get("synthesis")
    extracted_notes = state.get("extracted_notes", [])
    
    if synthesis:
        # We have synthesis, generate partial answer
        return {
            "final_answer": f"## Partial Results (Error occurred at {current_step})\n\n"
                          f"The research was partially completed. Error: {error}\n\n"
                          f"Available findings may be incomplete.",
            "should_continue": False
        }
    
    if extracted_notes:
        # We have notes, provide raw summary
        summary = "## Partial Research Notes\n\n"
        summary += f"Error occurred at {current_step}: {error}\n\n"
        summary += "### Raw Notes from Sources:\n"
        for notes in extracted_notes[:3]:
            summary += f"\n**{notes.get('title', 'Unknown')}**\n"
            for claim in notes.get('key_claims', [])[:3]:
                summary += f"- {claim}\n"
        
        return {
            "final_answer": summary,
            "citations": [n.get("url") for n in extracted_notes],
            "should_continue": False
        }
    
    # No usable data
    return {
        "final_answer": f"## Research Failed\n\n"
                       f"Unable to complete research. Error at {current_step}: {error}\n\n"
                       f"Please try rephrasing your question or try again later.",
        "citations": [],
        "should_continue": False
    }


# ============================================================================
# Build the Graph
# ============================================================================

def create_research_graph() -> StateGraph:
    """
    Create the LangGraph workflow for research.
    
    Flow:
    User Question → Planner → Search → Reader → Verifier → Synthesizer → Answer
    
    With error handling and fallbacks at each step.
    """
    # Initialize graph with state schema
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("search", search_node)
    workflow.add_node("reader", reader_node)
    workflow.add_node("verifier", verification_node)
    workflow.add_node("synthesizer", synthesis_node)
    workflow.add_node("answer", answer_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add conditional edges from planner
    workflow.add_conditional_edges(
        "planner",
        lambda state: "error_handler" if state.get("error_state") else "search",
        {
            "search": "search",
            "error_handler": "error_handler"
        }
    )
    
    # Add conditional edges from search
    workflow.add_conditional_edges(
        "search",
        lambda state: "error_handler" if state.get("error_state") and not state.get("search_results") else "reader",
        {
            "reader": "reader",
            "error_handler": "error_handler"
        }
    )
    
    # Add conditional edges from reader
    workflow.add_conditional_edges(
        "reader",
        lambda state: "error_handler" if state.get("error_state") and not state.get("extracted_notes") else "verifier",
        {
            "verifier": "verifier",
            "error_handler": "error_handler"
        }
    )
    
    # Add conditional edges from verifier
    workflow.add_conditional_edges(
        "verifier",
        lambda state: "error_handler" if state.get("error_state") else "synthesizer",
        {
            "synthesizer": "synthesizer",
            "error_handler": "error_handler"
        }
    )
    
    # Add conditional edges from synthesizer
    workflow.add_conditional_edges(
        "synthesizer",
        lambda state: "error_handler" if state.get("error_state") else "answer",
        {
            "answer": "answer",
            "error_handler": "error_handler"
        }
    )
    
    # Answer and error_handler go to END
    workflow.add_edge("answer", END)
    workflow.add_edge("error_handler", END)
    
    return workflow


def compile_research_agent():
    """Compile the research graph into a runnable agent."""
    graph = create_research_graph()
    return graph.compile()


# ============================================================================
# Run Research Function
# ============================================================================

def run_research(question: str, verbose: bool = False) -> dict:
    """
    Execute the research pipeline for a given question.
    
    Args:
        question: The user's research question
        verbose: Whether to print intermediate steps
    
    Returns:
        Dictionary with final_answer, citations, and metadata
    """
    agent = compile_research_agent()
    
    initial_state = {
        "user_question": question,
        "current_step": "plan",
        "retry_count": 0,
        "max_retries": 2,
        "search_results": [],
        "extracted_notes": [],
        "failures": [],
        "citations": [],
        "should_continue": True
    }
    
    if verbose:
        print(f"🔍 Starting research: {question}\n")
        print("=" * 60)
    
    # Run the graph
    final_state = None
    for step_output in agent.stream(initial_state):
        if verbose:
            for node_name, node_output in step_output.items():
                print(f"\n📌 Step: {node_name}")
                if node_output.get("current_step"):
                    print(f"   Next: {node_output['current_step']}")
                if node_output.get("error_state"):
                    print(f"   ⚠️ Error: {node_output['error_state']}")
        
        # Keep track of final state
        for node_output in step_output.values():
            if final_state is None:
                final_state = dict(initial_state)
            final_state.update(node_output)
    
    if verbose:
        print("\n" + "=" * 60)
        print("✅ Research complete!\n")
    
    return {
        "answer": final_state.get("final_answer", "No answer generated"),
        "citations": final_state.get("citations", []),
        "plan": final_state.get("research_plan"),
        "sources_used": len(final_state.get("extracted_notes", [])),
        "failures": final_state.get("failures", [])
    }
