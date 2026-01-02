"""
LangChain memory management for Q&A conversations.

Memory is scoped per case analysis and only used for conversation flow.
It never sees raw case text, pipeline prompts, or overrides context builder.
"""

from typing import Optional, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_community.chat_message_histories import ChatMessageHistory


# Session state key for QnA memory
QNA_MEMORY_KEY = "qna_conversation_memory"


class ConversationBufferMemory:
    """
    Simple buffer memory implementation compatible with LangChain interface.
    Wraps ChatMessageHistory to provide ConversationBufferMemory-like API.
    This avoids dependency on langchain.memory which may not be available.
    """
    def __init__(self):
        self.chat_memory = ChatMessageHistory()
    
    def save_context(self, inputs: dict, outputs: dict) -> None:
        """Save a conversation turn to memory."""
        question = inputs.get("question", "")
        answer = outputs.get("answer", "")
        if question:
            self.chat_memory.add_user_message(question)
        if answer:
            self.chat_memory.add_ai_message(answer)
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages in the conversation."""
        return self.chat_memory.messages
    
    def clear(self) -> None:
        """Clear all messages."""
        self.chat_memory.clear()


def get_qna_memory() -> Optional[ConversationBufferMemory]:
    """
    Get the Q&A conversation memory from session state.
    Returns None if no memory exists (new case or cleared).
    """
    import streamlit as st
    
    if QNA_MEMORY_KEY not in st.session_state:
        return None
    
    return st.session_state[QNA_MEMORY_KEY]


def init_qna_memory() -> ConversationBufferMemory:
    """
    Initialize a new Q&A conversation memory.
    Creates a fresh memory instance for a new case analysis.
    """
    import streamlit as st
    
    # Create new ConversationBufferMemory
    # This keeps the last N conversation turns
    memory = ConversationBufferMemory()
    
    # Store in session state
    st.session_state[QNA_MEMORY_KEY] = memory
    
    return memory


def clear_qna_memory() -> None:
    """
    Clear the Q&A conversation memory.
    Called when:
    - User analyzes a new case
    - User clicks "Reset analysis"
    """
    import streamlit as st
    
    if QNA_MEMORY_KEY in st.session_state:
        del st.session_state[QNA_MEMORY_KEY]


def save_qna_turn(question: str, answer: str) -> None:
    """
    Save a Q&A turn to memory.
    
    Args:
        question: User's question
        answer: AI's answer
    """
    memory = get_qna_memory()
    
    if memory is None:
        # Initialize memory if it doesn't exist
        memory = init_qna_memory()
    
    # Save the conversation turn
    # Using save_context ensures proper message formatting
    memory.save_context(
        inputs={"question": question},
        outputs={"answer": answer}
    )


def get_memory_summary(memory: Optional[ConversationBufferMemory]) -> str:
    """
    Get a summary of previous Q&A turns for the prompt.
    Returns empty string if no memory exists.
    
    This is used to provide conversational context without
    exposing raw case data or pipeline artifacts.
    """
    if memory is None:
        return ""
    
    # Get chat history from memory
    # Access messages through the messages property
    chat_history = memory.messages
    
    if not chat_history:
        return ""
    
    # Format previous Q&A turns for the prompt
    # Only include the last few turns to avoid token bloat
    MAX_TURNS = 3  # Keep last 3 Q&A pairs
    
    recent_turns = chat_history[-MAX_TURNS * 2:] if len(chat_history) > MAX_TURNS * 2 else chat_history
    
    summary_lines = ["Previous questions and answers:"]
    
    i = 0
    while i < len(recent_turns):
        if isinstance(recent_turns[i], HumanMessage):
            question = recent_turns[i].content
            if i + 1 < len(recent_turns) and isinstance(recent_turns[i + 1], AIMessage):
                answer = recent_turns[i + 1].content
                # Truncate long answers for summary
                if len(answer) > 200:
                    answer = answer[:200] + "..."
                summary_lines.append(f"- Q: {question}")
                summary_lines.append(f"  A: {answer}")
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    return "\n".join(summary_lines) if len(summary_lines) > 1 else ""
