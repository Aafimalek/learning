import json
from pathlib import Path
from typing import Dict, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from llm import get_llm
from qna.qna_memory import get_qna_memory, get_memory_summary, save_qna_turn, ConversationBufferMemory


# -------------------------
# Q&A Prompt Loading
# -------------------------

def load_qna_prompt() -> str:
    """
    Load the Q&A system prompt from the prompts file.
    """
    prompt_path = Path(__file__).parent / "qna_prompts.txt"
    
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"QnA prompt file not found: {prompt_path}"
        )
    
    return prompt_path.read_text(encoding="utf-8").strip()


# -------------------------
# Q&A Engine
# -------------------------

def answer_question(
    question: str,
    context: Dict[str, Any],
    memory: Optional[ConversationBufferMemory] = None
) -> str:
    """
    Answer a user question strictly from provided context.
    
    Args:
        question: User's question
        context: Structured context from context_builder (facts, issues, judgment)
        memory: Optional LangChain conversation memory for Q&A flow
    
    Returns:
        Answer string
    
    Important:
        - Memory is only used for conversation flow, NOT for facts
        - Context is the primary source of truth
        - Memory never overrides context builder
    """

    if not question.strip():
        raise ValueError("Question cannot be empty")

    if not context:
        return "No case context is available to answer this question."

    try:
        system_prompt = load_qna_prompt()
    except FileNotFoundError as e:
        # Fallback to a basic prompt if file is missing
        system_prompt = (
            "You are a legal Q&A assistant. Answer questions using only the provided context. "
            "Do not introduce new facts or perform fresh legal analysis. "
            "If the answer is not in the context, say so clearly."
        )

    # Get memory summary if memory exists
    # This provides conversational context without exposing raw case data
    memory_summary = ""
    if memory is not None:
        memory_summary = get_memory_summary(memory)
        if memory_summary:
            memory_summary = f"\n\n{memory_summary}\n"

    llm = get_llm()

    # Build prompt with memory context (if available)
    # Structure: system prompt + previous Q&A (if any) + current context + new question
    prompt_messages = [("system", system_prompt)]
    
    # Add memory summary if available (conversational context only)
    if memory_summary:
        prompt_messages.append(("human", f"Previous conversation:{memory_summary}"))
    
    # Add current context and question
    prompt_messages.append(
        (
            "human",
            "Current case context:\n{context}\n\nNew question:\n{question}"
        )
    )

    prompt = ChatPromptTemplate.from_messages(prompt_messages)

    chain = prompt | llm | StrOutputParser()

    try:
        response = chain.invoke(
            {
                "context": json.dumps(context, ensure_ascii=False, indent=2),
                "question": question
            }
        )
        
        if not response or not response.strip():
            return "I received an empty response. Please try rephrasing your question."
        
        answer = response.strip()
        
        # Save Q&A turn to memory (if memory exists)
        # This enables follow-up questions and conversational continuity
        if memory is not None:
            save_qna_turn(question, answer)
        
        return answer
        
    except Exception as e:
        # Provide user-friendly error message
        error_msg = (
            f"An error occurred while generating the answer: {str(e)}\n"
            "Please try again or rephrase your question."
        )
        raise RuntimeError(error_msg) from e
