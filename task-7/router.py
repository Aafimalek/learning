"""
Routing Policy Node.

This is a DETERMINISTIC Python function, not an LLM.
The LLM should NOT decide everything - this is where reliability comes from.

Routing Logic:
- confidence < threshold → CLARIFY_AGENT
- intent == X → X_AGENT
"""

from typing import Literal
from schemas import GraphState, IntentType, LogEntry, RoutingConfig


# ============================================================================
# Routing Policy (Pure Python, No LLM)
# ============================================================================

def routing_policy(
    state: GraphState,
    config: RoutingConfig = RoutingConfig()
) -> str:
    """
    Deterministic routing policy.
    
    This function encodes guardrails explicitly:
    - LLMs are probabilistic
    - LangGraph lets us add deterministic rules
    - This is where reliability comes from
    
    Returns the name of the next node to route to.
    """
    classification = state.get("classification")
    
    # Safety check - no classification means clarify
    if classification is None:
        return "clarify_agent"
    
    confidence = classification.confidence
    intent = classification.intent
    
    # Rule 1: Low confidence → Always clarify
    if confidence < config.confidence_threshold:
        return "clarify_agent"
    
    # Rule 2: Route based on intent
    route_map = {
        IntentType.BLOG_WRITE: "blog_agent",
        IntentType.CODE: "code_agent",
        IntentType.QNA: "qna_agent",
        IntentType.RESEARCH: "research_agent",
        IntentType.CLARIFY: "clarify_agent"
    }
    
    return route_map.get(intent, "clarify_agent")


def router_node(state: GraphState) -> dict:
    """
    Router node for LangGraph.
    
    Applies the routing policy and logs the decision.
    """
    route = routing_policy(state)
    
    classification = state.get("classification")
    
    log_entry = LogEntry(
        step="router",
        classified_intent=classification.intent if classification else None,
        confidence=classification.confidence if classification else None,
        chosen_route=route,
        metadata={
            "threshold": RoutingConfig().confidence_threshold,
            "reasoning": classification.reasoning if classification else "No classification"
        }
    ).model_dump()
    
    return {
        "routed_to": route,
        "logs": [log_entry]
    }


def get_next_node(state: GraphState) -> str:
    """
    Conditional edge function for LangGraph.
    Returns the node name to route to.
    """
    return state.get("routed_to", "clarify_agent")


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    from schemas import ClassificationResult
    
    # Test cases
    test_cases = [
        ClassificationResult(intent=IntentType.BLOG_WRITE, confidence=0.9, reasoning="Clear blog request"),
        ClassificationResult(intent=IntentType.CODE, confidence=0.8, reasoning="Code generation"),
        ClassificationResult(intent=IntentType.QNA, confidence=0.5, reasoning="Ambiguous question"),
        ClassificationResult(intent=IntentType.RESEARCH, confidence=0.3, reasoning="Very unclear"),
    ]
    
    for case in test_cases:
        state = {"classification": case}
        route = routing_policy(state)
        print(f"Intent: {case.intent}, Confidence: {case.confidence} → Route: {route}")
