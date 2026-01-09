"""
State schemas for the research agent system.
Defines three types of state:
- Short-term state: Current task, retries, tool outputs
- Research memory: Notes per source, intermediate conclusions
- Failure memory: Failed URLs, bad queries
"""

from typing import TypedDict, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Tool Response Schema - All tools return this format
# ============================================================================

class ToolResponse(BaseModel):
    """Standardized response from all tools. Never throw exceptions up the stack."""
    success: bool
    data: Optional[dict | list | str] = None
    error: Optional[str] = None
    retry_suggestion: Optional[str] = None


# ============================================================================
# Search Result Schemas
# ============================================================================

class SearchResult(BaseModel):
    """Metadata captured for each search result."""
    url: str
    title: str
    source: str = ""
    publication_date: Optional[str] = None
    snippet: str
    confidence_hint: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"


class SearchResults(BaseModel):
    """Collection of search results for a query."""
    query: str
    results: list[SearchResult] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Reader/Extraction Schemas
# ============================================================================

class ExtractedNotes(BaseModel):
    """
    Notes extracted from a single source.
    These are NOTES, not summaries - raw extraction for later synthesis.
    """
    url: str
    title: str
    key_claims: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    data_stats: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    author_bias: Optional[str] = None
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    extraction_method: Literal["FULL", "SNIPPET_ONLY", "FAILED"] = "FULL"


# ============================================================================
# Planner Schemas
# ============================================================================

class ResearchPlan(BaseModel):
    """Output from the Planner agent."""
    objective: str
    sub_questions: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    quality_constraints: list[str] = Field(default_factory=list)
    max_searches: int = 5
    max_articles_per_search: int = 3


# ============================================================================
# Verification Schemas
# ============================================================================

class VerificationResult(BaseModel):
    """Output from the Verification layer."""
    confirmed_points: list[str] = Field(default_factory=list)
    disputed_points: list[str] = Field(default_factory=list)
    single_source_claims: list[str] = Field(default_factory=list)
    source_agreement_score: float = 0.0  # 0-1 scale


# ============================================================================
# Synthesis Schemas
# ============================================================================

class SynthesizedFinding(BaseModel):
    """A single synthesized finding across sources."""
    finding: str
    evidence_strength: Literal["STRONG", "MODERATE", "WEAK"] = "MODERATE"
    supporting_sources: list[str] = Field(default_factory=list)
    contradicting_sources: list[str] = Field(default_factory=list)


class SynthesisResult(BaseModel):
    """Final synthesis output."""
    findings: list[SynthesizedFinding] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    confidence_summary: str = ""


# ============================================================================
# Failure Memory
# ============================================================================

class FailureRecord(BaseModel):
    """Record of a failed operation for learning."""
    operation: str  # "search", "read", "parse"
    target: str  # URL or query
    error: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    retries_attempted: int = 0


# ============================================================================
# Main Agent State (LangGraph TypedDict)
# ============================================================================

class AgentState(TypedDict, total=False):
    """
    Main state object that flows through the LangGraph.
    
    Short-term state: messages, current_step, retry_count, tool_outputs
    Research memory: research_plan, search_results, extracted_notes, verification, synthesis
    Failure memory: failures
    """
    # Input
    user_question: str
    
    # Short-term state
    current_step: str
    retry_count: int
    max_retries: int
    
    # Research memory
    research_plan: Optional[dict]  # ResearchPlan as dict
    search_results: list[dict]  # List of SearchResults as dicts
    extracted_notes: list[dict]  # List of ExtractedNotes as dicts
    verification: Optional[dict]  # VerificationResult as dict
    synthesis: Optional[dict]  # SynthesisResult as dict
    
    # Failure memory
    failures: list[dict]  # List of FailureRecord as dicts
    
    # Output
    final_answer: Optional[str]
    citations: list[str]
    
    # Control flow
    should_continue: bool
    error_state: Optional[str]
