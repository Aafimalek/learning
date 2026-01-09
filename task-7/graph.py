"""
LangGraph Workflow for Multi-Agent Routing System.

Graph Topology (Fan-out, not chain-of-thought):

    START
      ↓
IntentClassifier
      ↓
    Router (conditional edges)
   ↙  ↓   ↓   ↓   ↘
BLOG CODE QNA RESEARCH CLARIFY
   ↘  ↓   ↓   ↓   ↙
      ↓
     END

LangGraph strengths exploited:
- Conditional edges
- State passing (intent, confidence, metadata)
- Easy insertion of fallback paths
"""

from typing import Literal
from langgraph.graph import StateGraph, END, START

from schemas import GraphState, IntentType, LogEntry
from classifier import classifier_node
from router import router_node, get_next_node
from agents import (
    blog_agent_node,
    code_agent_node,
    qna_agent_node,
    research_agent_node,
    clarify_agent_node,
    error_recovery_node
)


# ============================================================================
# Conditional Edge Functions
# ============================================================================

def should_recover(state: GraphState) -> Literal["recover", "end"]:
    """Check if we need error recovery."""
    if state.get("error_state") and state.get("retry_count", 0) < state.get("max_retries", 2):
        return "recover"
    return "end"


def route_to_agent(state: GraphState) -> str:
    """
    Conditional edge function - routes to the appropriate agent.
    
    This is the core routing logic based on the router node's decision.
    """
    routed_to = state.get("routed_to", "clarify_agent")
    
    # Map route names to node names
    valid_routes = {
        "blog_agent": "blog_agent",
        "code_agent": "code_agent",
        "qna_agent": "qna_agent",
        "research_agent": "research_agent",
        "clarify_agent": "clarify_agent"
    }
    
    return valid_routes.get(routed_to, "clarify_agent")


# ============================================================================
# Graph Construction
# ============================================================================

def create_routing_graph() -> StateGraph:
    """
    Create the multi-agent routing graph.
    
    Structure:
    1. Classifier - Determines intent
    2. Router - Applies routing policy
    3. Specialized Agents - Handle specific intents
    4. Error Recovery - Handles failures
    """
    
    # Initialize graph with state schema
    graph = StateGraph(GraphState)
    
    # =========================================
    # Add Nodes
    # =========================================
    
    # Classification and routing
    graph.add_node("classifier", classifier_node)
    graph.add_node("router", router_node)
    
    # Specialized agents
    graph.add_node("blog_agent", blog_agent_node)
    graph.add_node("code_agent", code_agent_node)
    graph.add_node("qna_agent", qna_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("clarify_agent", clarify_agent_node)
    
    # Error handling
    graph.add_node("error_recovery", error_recovery_node)
    
    # =========================================
    # Add Edges
    # =========================================
    
    # Start → Classifier
    graph.add_edge(START, "classifier")
    
    # Classifier → Router
    graph.add_edge("classifier", "router")
    
    # Router → Agents (conditional edges)
    graph.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "blog_agent": "blog_agent",
            "code_agent": "code_agent",
            "qna_agent": "qna_agent",
            "research_agent": "research_agent",
            "clarify_agent": "clarify_agent"
        }
    )
    
    # Agents → End or Error Recovery
    for agent in ["blog_agent", "code_agent", "qna_agent", "research_agent", "clarify_agent"]:
        graph.add_conditional_edges(
            agent,
            should_recover,
            {
                "recover": "error_recovery",
                "end": END
            }
        )
    
    # Error Recovery → Clarify or End
    graph.add_conditional_edges(
        "error_recovery",
        lambda state: "clarify_agent" if state.get("routed_to") == "clarify_agent" else END,
        {
            "clarify_agent": "clarify_agent",
            END: END
        }
    )
    
    return graph


def compile_graph():
    """Compile the graph for execution."""
    graph = create_routing_graph()
    return graph.compile()


# ============================================================================
# Graph Execution Helper
# ============================================================================

def run_query(query: str, max_retries: int = 2) -> dict:
    """
    Execute a query through the routing graph.
    
    Args:
        query: User's input query
        max_retries: Maximum retry attempts on failure
        
    Returns:
        Final state with agent response and logs
    """
    app = compile_graph()
    
    initial_state: GraphState = {
        "user_query": query,
        "classification": None,
        "routed_to": None,
        "agent_response": None,
        "error_state": None,
        "retry_count": 0,
        "max_retries": max_retries,
        "logs": [],
        "should_continue": True
    }
    
    # Execute graph
    final_state = app.invoke(initial_state)
    
    return final_state


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    # Quick test
    test_queries = [
        "Write a blog about machine learning",
        "Write a Python function to reverse a string",
        "What is gradient descent?",
        "Compare CNN vs RNN",
        "hello"  # Ambiguous - should clarify
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        result = run_query(query)
        
        if result.get("agent_response"):
            response = result["agent_response"]
            print(f"Agent: {response.agent_type}")
            print(f"Success: {response.success}")
            if response.raw_output:
                preview = response.raw_output[:200] + "..." if len(response.raw_output) > 200 else response.raw_output
                print(f"Output Preview: {preview}")
