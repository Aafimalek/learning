"""
State schemas for the multi-agent routing system.

Intent Table (Contract):
┌────────────┬─────────────────────────────────┬──────────────────┬─────────────────────────────────┐
│ Intent     │ Description                     │ Output Shape     │ Example                         │
├────────────┼─────────────────────────────────┼──────────────────┼─────────────────────────────────┤
│ BLOG_WRITE │ Long-form creative writing      │ Markdown article │ "Write a blog on transformers"  │
│ CODE       │ Deterministic code generation   │ Code block       │ "Write a Flask API"             │
│ QNA        │ Short factual answer            │ Text             │ "What is cosine similarity?"    │
│ RESEARCH   │ In-depth analysis with sources  │ Structured text  │ "Explain RLHF with examples"    │
│ CLARIFY    │ Ambiguous query needs clarity   │ Question         │ (internal routing)              │
└────────────┴─────────────────────────────────┴──────────────────┴─────────────────────────────────┘

Rule: If two intents can answer the same query, they must be split or merged.
"""

from typing import TypedDict, Optional, Literal, Annotated
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import operator


# ============================================================================
# Intent Definitions
# ============================================================================

class IntentType(str, Enum):
    """All possible intents in the system. Non-overlapping by design."""
    BLOG_WRITE = "BLOG_WRITE"   # Long-form creative content
    CODE = "CODE"               # Code generation
    QNA = "QNA"                 # Quick factual answers
    RESEARCH = "RESEARCH"       # In-depth analysis
    CLARIFY = "CLARIFY"         # Needs clarification (fallback)


# ============================================================================
# Classifier Output Schema (Structured Output)
# ============================================================================

class ClassificationResult(BaseModel):
    """
    Output from the intent classifier.
    This is the ONLY output format accepted from the classifier LLM.
    """
    intent: IntentType = Field(
        description="The classified intent type"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score between 0 and 1"
    )
    reasoning: str = Field(
        description="Short explanation for debugging (1-2 sentences)"
    )


# ============================================================================
# Agent Output Schemas
# ============================================================================

class BlogOutput(BaseModel):
    """Output from the blog writing agent."""
    title: str
    content: str  # Markdown format
    word_count: int
    tags: list[str] = Field(default_factory=list)


class CodeOutput(BaseModel):
    """Output from the code generation agent."""
    language: str
    code: str
    explanation: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)


class QNAOutput(BaseModel):
    """Output from the QNA agent."""
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)


class ResearchOutput(BaseModel):
    """Output from the research agent."""
    summary: str
    key_points: list[str] = Field(default_factory=list)
    sources_consulted: int = 0


class ClarificationOutput(BaseModel):
    """Output from the clarification agent."""
    clarifying_question: str
    options: list[str] = Field(default_factory=list)
    original_query: str


# ============================================================================
# Unified Agent Response
# ============================================================================

class AgentResponse(BaseModel):
    """Standardized response from any agent."""
    success: bool
    agent_type: IntentType
    output: Optional[BlogOutput | CodeOutput | QNAOutput | ResearchOutput | ClarificationOutput] = None
    raw_output: Optional[str] = None  # Fallback if structured parsing fails
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


# ============================================================================
# Log Entry Schema
# ============================================================================

class LogEntry(BaseModel):
    """Single log entry for introspection."""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    step: str
    query: Optional[str] = None
    classified_intent: Optional[IntentType] = None
    confidence: Optional[float] = None
    chosen_route: Optional[str] = None
    output_length: Optional[int] = None
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


# ============================================================================
# Graph State (LangGraph TypedDict)
# ============================================================================

class GraphState(TypedDict):
    """
    State passed through the LangGraph workflow.
    
    This is the central state object that flows through all nodes.
    Uses Annotated with operator.add for list accumulation.
    """
    # Input
    user_query: str
    
    # Classification
    classification: Optional[ClassificationResult]
    
    # Routing
    routed_to: Optional[str]
    
    # Agent output
    agent_response: Optional[AgentResponse]
    
    # Error handling
    error_state: Optional[str]
    retry_count: int
    max_retries: int
    
    # Logging (accumulates with each step)
    logs: Annotated[list[dict], operator.add]
    
    # Control flow
    should_continue: bool


# ============================================================================
# Configuration
# ============================================================================

class RoutingConfig(BaseModel):
    """Configuration for the routing policy."""
    confidence_threshold: float = Field(
        default=0.6,
        description="Minimum confidence to route to specialized agent"
    )
    max_retries: int = Field(
        default=2,
        description="Maximum retry attempts on failure"
    )
    enable_logging: bool = Field(
        default=True,
        description="Enable detailed logging"
    )
