import streamlit as st
from chains import get_chat_chain
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="LangChain Chatbot", layout="centered")

st.title("💬 LangChain Chat Model Chatbot")

# Initialize chain once per session
if "chain" not in st.session_state:
    st.session_state.chain = get_chat_chain()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Ask something...")

if user_input:
    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    with st.chat_message("user"):
        st.markdown(user_input)

    # Invoke LangChain with chat history
    response = st.session_state.chain.invoke({
        "input": user_input,
        "chat_history": st.session_state.chat_history
    })

    # Extract content from AIMessage
    bot_reply = response.content if hasattr(response, 'content') else str(response)

    # Update chat history
    st.session_state.chat_history.append(HumanMessage(content=user_input))
    st.session_state.chat_history.append(AIMessage(content=bot_reply))

    # Show assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": bot_reply}
    )
    with st.chat_message("assistant"):
        st.markdown(bot_reply)