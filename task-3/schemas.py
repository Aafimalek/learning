from typing import List, Dict, Literal
from pydantic import BaseModel, Field


# -------------------------
# Stage 1: Case Understanding
# -------------------------

class CaseUnderstanding(BaseModel):
    summary: str = Field(
        ...,
        description="Plain-language summary of the case"
    )
    parties: List[str] = Field(
        ...,
        description="List of parties involved in the case"
    )
    timeline: List[str] = Field(
        ...,
        description="Chronological sequence of key events"
    )
    ambiguities: List[str] = Field(
        ...,
        description="Facts that are unclear, disputed, or missing"
    )


# -------------------------
# Stage 2: Fact Extraction
# -------------------------

class ExtractedFacts(BaseModel):
    material_facts: List[str] = Field(
        ...,
        description="Facts that directly affect legal outcome"
    )
    procedural_facts: List[str] = Field(
        ...,
        description="Court, jurisdiction, procedural posture if mentioned"
    )
    evidence: List[str] = Field(
        ...,
        description="Evidence explicitly referenced in the case"
    )


# -------------------------
# Stage 3: Issue Spotting
# -------------------------

class LegalIssues(BaseModel):
    issues: List[str] = Field(
        ...,
        description="Legal issues framed as clear questions"
    )


# -------------------------
# Stage 4: Arguments
# -------------------------

class ArgumentSide(BaseModel):
    points: List[str] = Field(
        ...,
        description="Key arguments supporting this side"
    )
    relied_facts: List[str] = Field(
        ...,
        description="Facts relied upon for these arguments"
    )


class IssueArguments(BaseModel):
    side_a: ArgumentSide = Field(
        ...,
        description="Plaintiff / Prosecution arguments"
    )
    side_b: ArgumentSide = Field(
        ...,
        description="Defendant arguments"
    )
    strength: Literal["weak", "moderate", "strong"] = Field(
        ...,
        description="Overall strength comparison"
    )


class ArgumentsByIssue(BaseModel):
    arguments: Dict[str, IssueArguments] = Field(
        ...,
        description="Arguments mapped per legal issue"
    )


# -------------------------
# Stage 5: Judgment Prediction
# -------------------------

class JudgmentPrediction(BaseModel):
    outcome: str = Field(
        ...,
        description="Likely judgment or disposition"
    )
    reasoning: str = Field(
        ...,
        description="Explanation weighing arguments issue-by-issue"
    )
    confidence: Literal["low", "medium", "high"] = Field(
        ...,
        description="Confidence level of prediction"
    )
    assumptions: List[str] = Field(
        ...,
        description="Key assumptions made due to missing or unclear facts"
    )
