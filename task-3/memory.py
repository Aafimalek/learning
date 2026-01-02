import streamlit as st

from config import MEMORY_KEY


def init_memory() -> None:
    """
    Initialize structured memory in Streamlit session state.
    Safe to call multiple times.
    """
    if MEMORY_KEY not in st.session_state:
        st.session_state[MEMORY_KEY] = {
            "understanding": None,
            "facts": None,
            "issues": None,
            "arguments": None,
            "judgment": None,
        }


def save_stage_output(stage: str, data) -> None:
    """
    Save output of a pipeline stage into memory.
    """
    if MEMORY_KEY not in st.session_state:
        init_memory()

    st.session_state[MEMORY_KEY][stage] = data


def get_memory(stage: str):
    """
    Retrieve stored output for a given stage.
    Returns None if not present.
    """
    if MEMORY_KEY not in st.session_state:
        return None

    return st.session_state[MEMORY_KEY].get(stage)


def clear_memory() -> None:
    """
    Clears all stored analysis.
    Useful when starting a completely new case.
    Also clears Q&A conversation memory to prevent cross-case contamination.
    """
    if MEMORY_KEY in st.session_state:
        st.session_state[MEMORY_KEY] = {
            "understanding": None,
            "facts": None,
            "issues": None,
            "arguments": None,
            "judgment": None,
        }
    
    # Clear Q&A conversation memory when clearing analysis
    from qna.qna_memory import clear_qna_memory
    clear_qna_memory()


def has_existing_analysis() -> bool:
    """
    Returns True if a prior case has already been analyzed.
    """
    if MEMORY_KEY not in st.session_state:
        return False

    memory = st.session_state[MEMORY_KEY]
    return memory.get("facts") is not None


def is_follow_up(follow_up_text: str) -> bool:
    """
    Determines whether the current input should be treated as a follow-up.
    A follow-up exists if:
    - User provided follow-up text
    - There is already an existing analysis in memory
    """
    if not follow_up_text:
        return False

    return has_existing_analysis()
