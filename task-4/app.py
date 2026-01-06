import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from backend import chatbot, add_thread_id, get_thread_ids

st.set_page_config(page_title="LangGraph Chatbot", page_icon="🤖")

st.title("LangGraph Chatbot")

# Initialize thread_id if not present
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Sidebar for chat history
with st.sidebar:
    st.header("Chat Sessions")
    
    if st.button("➕ New Chat"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()
        
    st.subheader("Recent Chats")
    existing_ids = get_thread_ids()
    reversed_ids = existing_ids[::-1] # Show newest first
    for tid in reversed_ids:
        # Use a label for the current chat or a button for others
        if tid == st.session_state.thread_id:
            st.button(f"📍 {tid}", disabled=True, key=f"curr_{tid}")
        else:
            if st.button(f"💬 {tid}", key=f"btn_{tid}"):
                st.session_state.thread_id = tid
                st.rerun()

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Fetch current state from memory
try:
    current_state = chatbot.get_state(config)
    # If the state exists, it will have 'messages'. If it's a new thread, values might be empty.
    messages = current_state.values.get("messages", [])
except Exception as e:
    # If there's an issue fetching state (e.g. invalid config or empty storage), start fresh
    messages = []

# Display chat history
for message in messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

# Handle user input
if prompt := st.chat_input("Type your message here..."):
    # Ensure thread is registered
    add_thread_id(st.session_state.thread_id)

    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        # Stream the response
        full_response = ""
        
        # Use stream_mode="messages" to get token-by-token updates
        for msg, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=prompt)]}, 
            config=config, 
            stream_mode="messages"
        ):
            if msg.content:
                full_response += msg.content
                message_placeholder.markdown(full_response + "▌")
        
        # Final update to remove the cursor
        message_placeholder.markdown(full_response)
        
        if not full_response:
             message_placeholder.markdown("No response generated.")
