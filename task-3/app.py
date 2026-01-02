import streamlit as st
from qna.context_builder import build_context
from qna.qna_engine import answer_question
from qna.qna_memory import init_qna_memory, get_qna_memory, clear_qna_memory

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will rely on system environment variables

from pipeline import (
    understand_case,
    extract_facts,
    identify_issues,
    generate_arguments,
    predict_judgment
)
from memory import (
    init_memory,
    save_stage_output,
    get_memory,
    is_follow_up
)

# -------------------------
# Streamlit page config
# -------------------------
st.set_page_config(
    page_title="Legal Case Analysis Assistant",
    layout="wide"
)

st.title("📚 Legal Case Analysis Assistant")
st.caption("Structured legal reasoning. Student-style analysis.")

# -------------------------
# Initialize memory
# -------------------------
init_memory()

# -------------------------
# Input section
# -------------------------
with st.form("case_form"):
    case_text = st.text_area(
        "Enter legal case description",
        height=250,
        placeholder="Paste the full case facts here..."
    )

    follow_up = st.text_input(
        "Follow-up question (optional)",
        placeholder="e.g. What if the agreement was oral?"
    )

    submitted = st.form_submit_button("Analyze")

# Reset button (outside form to work independently)
if st.button("🔄 Reset Analysis", help="Clear all analysis and start fresh"):
    from memory import clear_memory
    clear_memory()  # This also clears QnA memory
    st.success("Analysis reset. You can now start a new case.")
    st.rerun()

# -------------------------
# Main execution
# -------------------------
if submitted:
    if not case_text.strip():
        st.warning("Please provide a case description.")
        st.stop()

    with st.spinner("Analyzing case..."):

        # Check whether this is a follow-up
        follow_up_mode = is_follow_up(follow_up)

        # Initialize Q&A memory for new case analysis
        # Memory is scoped per case - new case = new memory
        if not follow_up_mode:
            # Clear any existing Q&A memory (new case analysis)
            clear_qna_memory()
            # Initialize fresh Q&A memory for this case
            init_qna_memory()

        # -------- Stage 1: Understand case --------
        if not follow_up_mode:
            understanding = understand_case(case_text)
            save_stage_output("understanding", understanding)
        else:
            understanding = get_memory("understanding")

        # -------- Stage 2: Extract facts --------
        if not follow_up_mode:
            facts = extract_facts(understanding)
            save_stage_output("facts", facts)
        else:
            facts = get_memory("facts")

        # -------- Stage 3: Identify issues --------
        issues = identify_issues(facts, follow_up)
        save_stage_output("issues", issues)

        # -------- Stage 4: Generate arguments --------
        arguments = generate_arguments(facts, issues)
        save_stage_output("arguments", arguments)

        # -------- Stage 5: Predict judgment --------
        judgment = predict_judgment(facts, issues, arguments)
        save_stage_output("judgment", judgment)

    st.success("Analysis complete")

# -------------------------
# Display analysis results (persist across reruns)
# -------------------------
# Check if we have analysis results in memory
understanding = get_memory("understanding")
facts = get_memory("facts")
issues = get_memory("issues")
arguments = get_memory("arguments")
judgment = get_memory("judgment")

if understanding and facts and issues and arguments and judgment:
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧠 Case Understanding")
        st.write(understanding["summary"])
        st.markdown("**Parties Involved:**")
        st.write(understanding["parties"])
        st.markdown("**Unclear / Disputed Facts:**")
        st.write(understanding["ambiguities"])

    with col2:
        st.subheader("📌 Extracted Facts")
        st.markdown("**Material Facts**")
        st.write(facts["material_facts"])
        st.markdown("**Procedural Facts**")
        st.write(facts["procedural_facts"])
        st.markdown("**Evidence**")
        st.write(facts["evidence"])

    st.divider()

    st.subheader("⚖️ Legal Issues")
    for idx, issue in enumerate(issues, start=1):
        st.markdown(f"**Issue {idx}:** {issue}")

    st.divider()

    st.subheader("🗣️ Arguments")

    for issue, argument_pair in arguments.items():
        st.markdown(f"### {issue}")

        st.markdown("**Plaintiff / Prosecution**")
        st.write(argument_pair["side_a"])

        st.markdown("**Defendant**")
        st.write(argument_pair["side_b"])

        st.markdown("**Strength Assessment**")
        st.write(argument_pair["strength"])

    st.divider()

    st.subheader("📜 Likely Judgment")
    st.markdown(f"**Predicted Outcome:** {judgment['outcome']}")
    st.markdown("**Reasoning:**")
    st.write(judgment["reasoning"])
    st.markdown(f"**Confidence Level:** {judgment['confidence']}")
    st.markdown("**Key Assumptions:**")
    st.write(judgment["assumptions"])
    
    st.divider()
    
    # -------------------------
    # Q&A Section (always visible when analysis exists)
    # -------------------------
    st.subheader("💬 Ask Questions About This Case")

    # Use a form for QnA to prevent page refresh on Enter
    with st.form("qna_form", clear_on_submit=False):
        qna_question = st.text_input(
            "Ask a question based on the above analysis",
            placeholder="e.g. Why is BrightMart's argument weaker?",
            key="qna_input"
        )
        qna_submitted = st.form_submit_button("Ask Question")

    # Store QnA answer in session state to persist it
    if "qna_answer" not in st.session_state:
        st.session_state.qna_answer = None
    if "qna_question" not in st.session_state:
        st.session_state.qna_question = None

    if qna_submitted and qna_question:
        with st.spinner("Answering from case context..."):
            try:
                # Build context from structured memory
                analysis_memory = {
                    "understanding": understanding,
                    "facts": facts,
                    "issues": issues,
                    "arguments": arguments,
                    "judgment": judgment,
                }

                context = build_context(
                    question=qna_question,
                    analysis_memory=analysis_memory
                )

                # Get Q&A conversation memory (scoped per case)
                qna_memory = get_qna_memory()

                answer = answer_question(
                    question=qna_question,
                    context=context,
                    memory=qna_memory  # Pass memory for conversational flow
                )

                # Store in session state to persist across reruns
                st.session_state.qna_answer = answer
                st.session_state.qna_question = qna_question
                
            except ValueError as e:
                st.error(f"Invalid question: {str(e)}")
                st.session_state.qna_answer = None
            except RuntimeError as e:
                st.error(f"Error generating answer: {str(e)}")
                st.session_state.qna_answer = None
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                st.info("Please try again or rephrase your question.")
                st.session_state.qna_answer = None

    # Display stored QnA answer if it exists
    if st.session_state.qna_answer and st.session_state.qna_question:
        st.markdown(f"**Question:** {st.session_state.qna_question}")
        st.markdown("**Answer:**")
        st.write(st.session_state.qna_answer)