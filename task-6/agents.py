"""
Agent nodes for the research pipeline.
Each node is a function that takes AgentState and returns partial AgentState update.
"""

import os
import json
from typing import Optional
from datetime import datetime

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from schemas import (
    AgentState, ResearchPlan, ExtractedNotes, 
    VerificationResult, SynthesizedFinding, SynthesisResult,
    FailureRecord, ToolResponse
)
from tools import get_search_tool, get_reader_tool


# ============================================================================
# LLM Configuration
# ============================================================================

def get_llm(temperature: float = 0.0) -> ChatGroq:
    """Get configured ChatGroq instance."""
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=temperature,
        max_tokens=4096,
    )


# ============================================================================
# Planner Node
# ============================================================================

PLANNER_SYSTEM_PROMPT = """You are a research planning agent. Your job is to convert vague user questions into concrete research plans.

Given a user question, you must output a structured research plan with:
1. Clear objective (what we're trying to learn)
2. Sub-questions (break down the main question into specific aspects)
3. Search queries (specific search terms to use, 3-5 queries)
4. Quality constraints (what makes a good source for this topic)

IMPORTANT:
- Generate multiple specific search queries, not one broad one
- Prefer authoritative sources (academic, government, established news)
- Consider recency requirements
- Think about what sources would be most reliable for this topic

Output ONLY valid JSON in this exact format:
{
    "objective": "string describing what we want to learn",
    "sub_questions": ["question 1", "question 2", ...],
    "search_queries": ["query 1", "query 2", ...],
    "quality_constraints": ["constraint 1", "constraint 2", ...],
    "max_searches": 5,
    "max_articles_per_search": 3
}"""


def planner_node(state: AgentState) -> dict:
    """
    Planner agent: reduce entropy before searching.
    Converts vague intent → concrete research plan.
    """
    user_question = state.get("user_question", "")
    
    if not user_question:
        return {
            "error_state": "No user question provided",
            "should_continue": False
        }
    
    try:
        llm = get_llm(temperature=0.1)
        
        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=f"User Question: {user_question}\n\nCreate a research plan:")
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Extract JSON from response
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        plan_data = json.loads(json_str)
        plan = ResearchPlan(**plan_data)
        
        return {
            "research_plan": plan.model_dump(),
            "current_step": "search",
            "should_continue": True
        }
        
    except json.JSONDecodeError as e:
        return {
            "error_state": f"Failed to parse planner response: {str(e)}",
            "should_continue": False
        }
    except Exception as e:
        return {
            "error_state": f"Planner failed: {str(e)}",
            "should_continue": False
        }


# ============================================================================
# Search Node
# ============================================================================

def search_node(state: AgentState) -> dict:
    """
    Search agent: breadth first, shallow.
    Executes search queries from the plan and collects results.
    """
    research_plan = state.get("research_plan")
    if not research_plan:
        return {
            "error_state": "No research plan available",
            "should_continue": False
        }
    
    plan = ResearchPlan(**research_plan)
    search_tool = get_search_tool()
    
    all_results = []
    failures = state.get("failures", [])
    
    for query in plan.search_queries[:plan.max_searches]:
        result = search_tool.search(
            query=query,
            max_results=plan.max_articles_per_search
        )
        
        if result.success:
            all_results.append(result.data)
        else:
            # Record failure but continue
            failures.append(FailureRecord(
                operation="search",
                target=query,
                error=result.error or "Unknown error",
                retries_attempted=2
            ).model_dump())
            
            # Try simplified query as fallback
            if result.retry_suggestion:
                simplified = " ".join(query.split()[:3])  # Take first 3 words
                retry_result = search_tool.search(query=simplified, max_results=3)
                if retry_result.success:
                    all_results.append(retry_result.data)
    
    if not all_results:
        return {
            "error_state": "All searches failed",
            "failures": failures,
            "should_continue": False
        }
    
    return {
        "search_results": all_results,
        "failures": failures,
        "current_step": "read",
        "should_continue": True
    }


# ============================================================================
# Reader Node
# ============================================================================

EXTRACTION_SYSTEM_PROMPT = """You are a research note-taker. Your job is to extract structured notes from article content.

DO NOT SUMMARIZE. Extract raw notes for later synthesis.

For the given article content, extract:
1. Key claims (main assertions made in the article)
2. Evidence (facts, studies, data supporting claims)
3. Data/stats (specific numbers, percentages, dates)
4. Limitations (caveats, acknowledged gaps, biases)
5. Author bias (if detectable - tone, affiliation, perspective)

Output ONLY valid JSON in this exact format:
{
    "key_claims": ["claim 1", "claim 2", ...],
    "evidence": ["evidence 1", "evidence 2", ...],
    "data_stats": ["stat 1", "stat 2", ...],
    "limitations": ["limitation 1", ...],
    "author_bias": "description or null"
}"""


def reader_node(state: AgentState) -> dict:
    """
    Reader agent: extract, don't summarize yet.
    Fetches articles and extracts structured notes.
    """
    search_results = state.get("search_results", [])
    if not search_results:
        return {
            "error_state": "No search results to read",
            "should_continue": False
        }
    
    reader_tool = get_reader_tool()
    llm = get_llm(temperature=0.0)
    
    all_notes = []
    failures = state.get("failures", [])
    seen_urls = set()
    
    for search_result in search_results:
        for item in search_result.get("results", []):
            url = item.get("url", "")
            
            # Skip duplicates
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Fetch article content
            fetch_result = reader_tool.fetch_article(
                url=url,
                snippet_fallback=item.get("snippet")
            )
            
            if not fetch_result.success:
                failures.append(FailureRecord(
                    operation="read",
                    target=url,
                    error=fetch_result.error or "Fetch failed"
                ).model_dump())
                continue
            
            article_data = fetch_result.data
            content = article_data.get("content", "")
            extraction_method = article_data.get("extraction_method", "FULL")
            
            # Extract notes using LLM
            try:
                messages = [
                    SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
                    HumanMessage(content=f"Article Title: {article_data.get('title', 'Unknown')}\n\nContent:\n{content[:8000]}\n\nExtract notes:")
                ]
                
                response = llm.invoke(messages)
                resp_content = response.content.strip()
                
                # Parse JSON
                json_str = resp_content
                if "```json" in resp_content:
                    json_str = resp_content.split("```json")[1].split("```")[0]
                elif "```" in resp_content:
                    json_str = resp_content.split("```")[1].split("```")[0]
                
                notes_data = json.loads(json_str)
                
                # Determine confidence
                confidence = item.get("confidence_hint", "MEDIUM")
                if extraction_method == "SNIPPET_ONLY":
                    confidence = "LOW"
                
                notes = ExtractedNotes(
                    url=url,
                    title=article_data.get("title", item.get("title", "")),
                    key_claims=notes_data.get("key_claims", []),
                    evidence=notes_data.get("evidence", []),
                    data_stats=notes_data.get("data_stats", []),
                    limitations=notes_data.get("limitations", []),
                    author_bias=notes_data.get("author_bias"),
                    confidence=confidence,
                    extraction_method=extraction_method
                )
                
                all_notes.append(notes.model_dump())
                
            except Exception as e:
                # Mark as low confidence with snippet only
                failures.append(FailureRecord(
                    operation="extract",
                    target=url,
                    error=str(e)
                ).model_dump())
                
                # Still include with snippet if available
                if item.get("snippet"):
                    notes = ExtractedNotes(
                        url=url,
                        title=item.get("title", ""),
                        key_claims=[item.get("snippet", "")],
                        confidence="LOW",
                        extraction_method="SNIPPET_ONLY"
                    )
                    all_notes.append(notes.model_dump())
    
    if not all_notes:
        return {
            "error_state": "Failed to extract notes from any source",
            "failures": failures,
            "should_continue": False
        }
    
    return {
        "extracted_notes": all_notes,
        "failures": failures,
        "current_step": "verify",
        "should_continue": True
    }


# ============================================================================
# Verification Node
# ============================================================================

VERIFICATION_SYSTEM_PROMPT = """You are a fact-checker and verification agent. Your job is to cross-check claims across multiple sources.

Given notes from multiple sources, identify:
1. Confirmed points (claims that multiple sources agree on)
2. Disputed points (claims where sources contradict each other)
3. Single-source claims (claims made by only one source - treat with caution)

Also assess overall source agreement (0-1 scale).

Output ONLY valid JSON in this exact format:
{
    "confirmed_points": ["point 1", "point 2", ...],
    "disputed_points": ["point 1 - Source A says X, Source B says Y", ...],
    "single_source_claims": ["claim from single source", ...],
    "source_agreement_score": 0.75
}"""


def verification_node(state: AgentState) -> dict:
    """
    Verification layer: cross-check before synthesis.
    This reduces hallucinations more than any prompt trick.
    """
    extracted_notes = state.get("extracted_notes", [])
    if not extracted_notes:
        return {
            "error_state": "No notes to verify",
            "should_continue": False
        }
    
    # Skip verification if only one source
    if len(extracted_notes) == 1: 
        notes = extracted_notes[0] 
        verification = VerificationResult(
            single_source_claims=notes.get("key_claims", []),
            source_agreement_score=0.0
        )
        return {
            "verification": verification.model_dump(),
            "current_step": "synthesize",
            "should_continue": True
        }
    
    try:
        llm = get_llm(temperature=0.0)
        
        # Format notes for verification
        notes_text = ""
        for i, notes in enumerate(extracted_notes, 1):
            notes_text += f"\n--- Source {i}: {notes.get('title', 'Unknown')} ---\n"
            notes_text += f"URL: {notes.get('url', 'Unknown')}\n"
            notes_text += f"Confidence: {notes.get('confidence', 'MEDIUM')}\n"
            notes_text += f"Key Claims: {json.dumps(notes.get('key_claims', []))}\n"
            notes_text += f"Evidence: {json.dumps(notes.get('evidence', []))}\n"
            notes_text += f"Data/Stats: {json.dumps(notes.get('data_stats', []))}\n"
        
        messages = [
            SystemMessage(content=VERIFICATION_SYSTEM_PROMPT),
            HumanMessage(content=f"Cross-check these sources:\n{notes_text}\n\nVerification:")
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Parse JSON
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        verification_data = json.loads(json_str)
        verification = VerificationResult(**verification_data)
        
        return {
            "verification": verification.model_dump(),
            "current_step": "synthesize",
            "should_continue": True
        }
        
    except Exception as e:
        # Continue without verification if it fails
        return {
            "verification": VerificationResult().model_dump(),
            "current_step": "synthesize",
            "should_continue": True
        }


# ============================================================================
# Synthesis Node
# ============================================================================

SYNTHESIS_SYSTEM_PROMPT = """You are a research synthesis agent. Your job is to synthesize findings ACROSS sources, not per source.

BAD: "Article A says..., Article B says..."
GOOD: "Across N sources, there is consensus that X. Two sources dispute Y, citing..."

Given verified findings, create a synthesis with:
1. Key findings (synthesized across sources with evidence strength)
2. Open questions (what remains unclear or needs more research)
3. Confidence summary (overall reliability assessment)

For each finding, indicate:
- Evidence strength: STRONG (multiple reliable sources), MODERATE (some agreement), WEAK (single/low-confidence source)
- Supporting sources
- Any contradicting sources

Output ONLY valid JSON in this exact format:
{
    "findings": [
        {
            "finding": "The main synthesis point",
            "evidence_strength": "STRONG|MODERATE|WEAK",
            "supporting_sources": ["url1", "url2"],
            "contradicting_sources": []
        }
    ],
    "open_questions": ["question 1", "question 2"],
    "confidence_summary": "Overall assessment of confidence in these findings"
}"""


def synthesis_node(state: AgentState) -> dict:
    """
    Synthesis agent: compress meaning, not text.
    Summarizes across sources, not per source.
    """
    extracted_notes = state.get("extracted_notes", [])
    verification = state.get("verification", {})
    
    if not extracted_notes:
        return {
            "error_state": "No notes to synthesize",
            "should_continue": False
        }
    
    try:
        llm = get_llm(temperature=0.1)
        
        # Format all notes and verification
        context = "=== EXTRACTED NOTES ===\n"
        for notes in extracted_notes:
            context += f"\nSource: {notes.get('title', 'Unknown')}\n"
            context += f"URL: {notes.get('url', '')}\n"
            context += f"Confidence: {notes.get('confidence', 'MEDIUM')}\n"
            context += f"Key Claims: {json.dumps(notes.get('key_claims', []))}\n"
            context += f"Evidence: {json.dumps(notes.get('evidence', []))}\n"
            context += f"Data/Stats: {json.dumps(notes.get('data_stats', []))}\n"
            context += f"Limitations: {json.dumps(notes.get('limitations', []))}\n"
        
        context += "\n=== VERIFICATION RESULTS ===\n"
        context += f"Confirmed Points: {json.dumps(verification.get('confirmed_points', []))}\n"
        context += f"Disputed Points: {json.dumps(verification.get('disputed_points', []))}\n"
        context += f"Single-Source Claims: {json.dumps(verification.get('single_source_claims', []))}\n"
        context += f"Source Agreement Score: {verification.get('source_agreement_score', 0)}\n"
        
        messages = [
            SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
            HumanMessage(content=f"{context}\n\nSynthesize findings:")
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Parse JSON
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        synthesis_data = json.loads(json_str)
        
        # Convert findings to proper format
        findings = []
        for f in synthesis_data.get("findings", []):
            findings.append(SynthesizedFinding(
                finding=f.get("finding", ""),
                evidence_strength=f.get("evidence_strength", "MODERATE"),
                supporting_sources=f.get("supporting_sources", []),
                contradicting_sources=f.get("contradicting_sources", [])
            ))
        
        synthesis = SynthesisResult(
            findings=findings,
            open_questions=synthesis_data.get("open_questions", []),
            confidence_summary=synthesis_data.get("confidence_summary", "")
        )
        
        return {
            "synthesis": synthesis.model_dump(),
            "current_step": "answer",
            "should_continue": True
        }
        
    except Exception as e:
        return {
            "error_state": f"Synthesis failed: {str(e)}",
            "should_continue": False
        }


# ============================================================================
# Answer Generation Node
# ============================================================================

ANSWER_SYSTEM_PROMPT = """You are a research assistant providing a final answer based on synthesized research findings.

Your answer should:
1. Directly address the user's original question
2. Present findings clearly with appropriate confidence levels
3. Cite sources for major claims
4. Acknowledge limitations and open questions
5. Be well-structured and readable

Format your answer in Markdown with:
- Clear section headers
- Bullet points for key findings
- Citations in [Source Title](URL) format
- A "Confidence & Limitations" section at the end"""


def answer_node(state: AgentState) -> dict:
    """
    Final answer generation with citations.
    """
    user_question = state.get("user_question", "")
    synthesis = state.get("synthesis", {})
    extracted_notes = state.get("extracted_notes", [])
    verification = state.get("verification", {})
    
    if not synthesis:
        return {
            "final_answer": "I was unable to complete the research due to errors in the synthesis stage.",
            "citations": [],
            "should_continue": False
        }
    
    try:
        llm = get_llm(temperature=0.2)
        
        # Build context for answer
        context = f"User Question: {user_question}\n\n"
        context += "=== SYNTHESIZED FINDINGS ===\n"
        
        findings = synthesis.get("findings", [])
        for f in findings:
            context += f"\n• Finding: {f.get('finding', '')}\n"
            context += f"  Evidence Strength: {f.get('evidence_strength', 'MODERATE')}\n"
            context += f"  Supporting Sources: {f.get('supporting_sources', [])}\n"
            if f.get('contradicting_sources'):
                context += f"  Contradicting Sources: {f.get('contradicting_sources', [])}\n"
        
        context += f"\nOpen Questions: {synthesis.get('open_questions', [])}\n"
        context += f"Confidence Summary: {synthesis.get('confidence_summary', '')}\n"
        
        context += "\n=== SOURCE DETAILS ===\n"
        for notes in extracted_notes:
            context += f"- {notes.get('title', 'Unknown')} ({notes.get('url', '')})\n"
        
        messages = [
            SystemMessage(content=ANSWER_SYSTEM_PROMPT),
            HumanMessage(content=f"{context}\n\nProvide a comprehensive answer:")
        ]
        
        response = llm.invoke(messages)
        final_answer = response.content.strip()
        
        # Extract citations
        citations = [notes.get("url", "") for notes in extracted_notes if notes.get("url")]
        
        return {
            "final_answer": final_answer,
            "citations": citations,
            "current_step": "complete",
            "should_continue": False
        }
        
    except Exception as e:
        # Fallback answer from synthesis
        fallback = "## Research Summary\n\n"
        findings = synthesis.get("findings", [])
        for f in findings:
            fallback += f"- {f.get('finding', '')}\n"
        
        if synthesis.get("open_questions"):
            fallback += "\n## Open Questions\n"
            for q in synthesis.get("open_questions", []):
                fallback += f"- {q}\n"
        
        return {
            "final_answer": fallback,
            "citations": [n.get("url", "") for n in extracted_notes],
            "should_continue": False
        }
