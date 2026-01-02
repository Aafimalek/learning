from typing import Dict, Any


# -------------------------
# Keyword buckets (simple, explicit)
# -------------------------

FACT_KEYWORDS = {
    "fact", "facts", "happened", "timeline", "event", "evidence", "dispute"
}

ISSUE_KEYWORDS = {
    "issue", "issues", "question", "legal question", "dispute"
}

ARGUMENT_KEYWORDS = {
    "argument", "arguments", "claim", "defense", "defence",
    "plaintiff", "defendant", "prosecution", "liable", "breach"
}

JUDGMENT_KEYWORDS = {
    "judgment", "judgement", "decision", "outcome", "result",
    "court", "likely", "win", "lose", "favored", "favoured"
}

EXPLANATION_KEYWORDS = {
    "why", "explain", "reason", "because", "how"
}


# -------------------------
# Context Builder
# -------------------------

def build_context(
    question: str,
    analysis_memory: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build a minimal, relevant context object for Q&A.

    Parameters:
    - question: user question
    - analysis_memory: structured outputs from the pipeline

    Returns:
    - context dictionary to be passed to qna_engine
    """

    question_lower = question.lower()
    context: Dict[str, Any] = {}

    # -------------------------
    # Always include high-level summary if available
    # -------------------------
    understanding = analysis_memory.get("understanding")
    if understanding and understanding.get("summary"):
        context["case_summary"] = understanding.get("summary")

    # -------------------------
    # Facts
    # -------------------------
    if any(word in question_lower for word in FACT_KEYWORDS):
        facts = analysis_memory.get("facts")
        if facts:
            context["material_facts"] = facts.get("material_facts")
            context["procedural_facts"] = facts.get("procedural_facts")
            context["evidence"] = facts.get("evidence")

    # -------------------------
    # Issues
    # -------------------------
    if any(word in question_lower for word in ISSUE_KEYWORDS):
        issues = analysis_memory.get("issues")
        if issues:
            context["legal_issues"] = issues

    # -------------------------
    # Arguments
    # -------------------------
    if any(word in question_lower for word in ARGUMENT_KEYWORDS):
        arguments = analysis_memory.get("arguments")
        if arguments:
            context["arguments"] = arguments

    # -------------------------
    # Judgment
    # -------------------------
    judgment_keywords = JUDGMENT_KEYWORDS.union(EXPLANATION_KEYWORDS)
    if any(word in question_lower for word in judgment_keywords):
        judgment = analysis_memory.get("judgment")
        if judgment:
            context["judgment"] = {
                "outcome": judgment.get("outcome"),
                "reasoning": judgment.get("reasoning"),
                "confidence": judgment.get("confidence"),
                "assumptions": judgment.get("assumptions"),
            }

    # -------------------------
    # Fallback: if context is still too empty or only has case_summary
    # -------------------------
    # Count non-empty context items (excluding case_summary)
    meaningful_keys = [k for k in context.keys() if k != "case_summary" and context[k]]
    
    if len(meaningful_keys) == 0:
        # Provide safe minimal context
        facts = analysis_memory.get("facts")
        judgment = analysis_memory.get("judgment")

        if facts and facts.get("material_facts"):
            context["material_facts"] = facts.get("material_facts")

        if judgment and judgment.get("outcome"):
            context["judgment"] = {
                "outcome": judgment.get("outcome"),
                "confidence": judgment.get("confidence"),
            }

    return context
