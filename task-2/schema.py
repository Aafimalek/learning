from pydantic import BaseModel, Field
from typing import List

class AssistantResponse(BaseModel):
    """The final validated output for the user."""
    reasoning: str = Field(description="Step-by-step logic used to solve the query.")
    answer: str = Field(description="The final concise answer to the user's question.")
    tools_used: List[str] = Field(description="List of tools accessed (e.g., wikipedia, ddg).")
    confidence: float = Field(description="Confidence score between 0 and 1.")