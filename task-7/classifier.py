"""
Intent Classifier Node.

This is NOT an agent. It is a pure classifier.
Characteristics:
- No tools
- Low temperature
- Structured output only
- Fast model (Groq)

This node answers only one question: "What should handle this?"
"""

import os
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from schemas import (
    GraphState, 
    ClassificationResult, 
    IntentType,
    LogEntry
)

load_dotenv()


# ============================================================================
# Classifier Prompt
# ============================================================================

CLASSIFIER_SYSTEM_PROMPT = """You are an intent classifier. Your ONLY job is to classify user queries into exactly one intent category.

## Intent Categories (Non-overlapping):

1. **BLOG_WRITE**: Long-form creative writing requests
   - Blog posts, articles, essays
   - Requires: multiple paragraphs, structure, creative tone
   - Example: "Write a blog about machine learning trends"

2. **CODE**: Code generation requests
   - Programming tasks, scripts, APIs, functions
   - Requires: actual executable code
   - Example: "Write a Python function to sort a list"

3. **QNA**: Quick factual questions
   - Definition questions, short explanations
   - Requires: concise, direct answer (1-3 sentences)
   - Example: "What is cosine similarity?"

4. **RESEARCH**: In-depth analysis requests
   - Comparisons, deep dives, multi-perspective analysis
   - Requires: structured analysis, examples, nuance
   - Example: "Compare transformers vs RNNs for NLP"

## Classification Rules:
- If the query asks for CODE explicitly → CODE
- If the query asks for a "blog", "article", or "post" → BLOG_WRITE
- If the query is a simple factual question → QNA
- If the query needs analysis, comparison, or explanation → RESEARCH
- When in doubt, prefer QNA over RESEARCH (simpler is better)

## Confidence Guidelines:
- 0.9-1.0: Crystal clear intent, explicit keywords
- 0.7-0.9: Clear intent, implicit but obvious
- 0.5-0.7: Ambiguous, could go multiple ways
- Below 0.5: Very unclear, likely needs clarification

Output strict JSON only. No prose, no markdown, no explanation outside the JSON."""


CLASSIFIER_HUMAN_PROMPT = """Classify this user query:

Query: {query}

Return JSON with: intent, confidence (0-1), reasoning (1 sentence)"""


# ============================================================================
# Classifier Node
# ============================================================================

def create_classifier_chain():
    """Create the classifier LLM chain with structured output."""
    
    llm = ChatGroq(
        model="llama-3.1-8b-instant",  # Fast, cheap model
        temperature=0.0,  # Deterministic
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    # Use structured output for guaranteed schema
    structured_llm = llm.with_structured_output(ClassificationResult)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", CLASSIFIER_SYSTEM_PROMPT),
        ("human", CLASSIFIER_HUMAN_PROMPT)
    ])
    
    return prompt | structured_llm


def classifier_node(state: GraphState) -> dict:
    """
    Intent classifier node for LangGraph.
    
    This is a pure classification node:
    - No tools
    - No side effects
    - Returns structured classification only
    """
    query = state["user_query"]
    
    try:
        chain = create_classifier_chain()
        result: ClassificationResult = chain.invoke({"query": query})
        
        # Create log entry
        log_entry = LogEntry(
            step="classifier",
            query=query,
            classified_intent=result.intent,
            confidence=result.confidence,
            metadata={"reasoning": result.reasoning}
        ).model_dump()
        
        return {
            "classification": result,
            "logs": [log_entry],
            "error_state": None
        }
        
    except Exception as e:
        # On classifier failure, default to CLARIFY with low confidence
        fallback = ClassificationResult(
            intent=IntentType.CLARIFY,
            confidence=0.0,
            reasoning=f"Classifier error: {str(e)}"
        )
        
        log_entry = LogEntry(
            step="classifier",
            query=query,
            error=str(e),
            metadata={"fallback": True}
        ).model_dump()
        
        return {
            "classification": fallback,
            "logs": [log_entry],
            "error_state": f"Classifier failed: {str(e)}"
        }


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    # Quick test
    test_queries = [
        "Write a blog post about transformer architecture",
        "Write a Python Flask API for user authentication",
        "What is cosine similarity?",
        "Compare BERT vs GPT for text classification",
        "hello"
    ]
    
    chain = create_classifier_chain()
    
    for query in test_queries:
        result = chain.invoke({"query": query})
        print(f"\nQuery: {query}")
        print(f"Intent: {result.intent}")
        print(f"Confidence: {result.confidence}")
        print(f"Reasoning: {result.reasoning}")
