import streamlit as st
import uuid
import asyncio
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from backend import graph, get_thread_ids, ingest_pdf, delete_thread, set_current_thread, get_thread_pdf_info
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite

# Monkeypatch aiosqlite.Connection.is_alive for langgraph compatibility
if not hasattr(aiosqlite.Connection, "is_alive"):
    def is_alive(self):
        return self._running and self._thread.is_alive()
    setattr(aiosqlite.Connection, "is_alive", is_alive)

st.set_page_config(page_title="LangGraph Chatbot", page_icon="🤖")

st.title("LangGraph Chatbot")

async def main():
    # Setup Async Checkpointer
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        chatbot = graph.compile(checkpointer=checkpointer)

        # Fetch existing threads
        existing_ids = await get_thread_ids()

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
            reversed_ids = existing_ids[::-1] # Show newest first
            for tid in reversed_ids:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    if tid == st.session_state.thread_id:
                        st.button(f"📍 {tid}", disabled=True, key=f"curr_{tid}")
                    else:
                        if st.button(f"💬 {tid}", key=f"btn_{tid}"):
                            st.session_state.thread_id = tid
                            st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{tid}"):
                         await delete_thread(tid)
                         # If deleting current thread, reset to new
                         if tid == st.session_state.thread_id:
                             st.session_state.thread_id = str(uuid.uuid4())
                         st.rerun()

            # File Uploader
            st.markdown("---")
            st.subheader("📄 Upload Document")
            
            # Show currently loaded PDF for this thread
            pdf_info = get_thread_pdf_info(st.session_state.thread_id)
            if pdf_info:
                cached_badge = " ⚡ cached" if pdf_info.get('cached') else ""
                st.info(f"📎 **Loaded:** {pdf_info['filename']}{cached_badge}\n\n({pdf_info['chunks']} chunks)")
            
            uploaded_file = st.file_uploader("Upload a PDF to chat with", type=["pdf"], key=f"uploader_{st.session_state.thread_id}")
            
            if uploaded_file:
                # Ingest the file if it hasn't been ingested for this thread yet (or re-ingest)
                if st.button("Process PDF"):
                    with st.spinner("Processing PDF..."):
                        try:
                            # Read bytes
                            file_bytes = uploaded_file.getvalue()
                            stats = ingest_pdf(file_bytes, st.session_state.thread_id, uploaded_file.name)
                            if stats.get('cached'):
                                st.success(f"⚡ Using cached embeddings for {stats['filename']} ({stats['chunks']} chunks)")
                            else:
                                st.success(f"✅ Indexed {stats['chunks']} chunks from {stats['filename']}")
                            st.rerun()  # Refresh to show the loaded PDF info
                        except Exception as e:
                            st.error(f"Error processing file: {e}")

        config = {"configurable": {"thread_id": st.session_state.thread_id},
                  "metadata": {"thread_id": st.session_state.thread_id},
                  "run_name":"chat_turn",
                  }
        
        # Set the current thread for RAG tool access
        set_current_thread(st.session_state.thread_id)
        
        # Fetch current state from memory
        try:
            current_state = await chatbot.aget_state(config)
            messages = current_state.values.get("messages", [])
        except Exception as e:
            messages = []

        # Display chat history
        for message in messages:
            if isinstance(message, HumanMessage):
                with st.chat_message("user"):
                    st.markdown(message.content)
            elif isinstance(message, AIMessage):
                with st.chat_message("assistant"):
                    st.markdown(message.content)
            # ToolMessages are usually not displayed in the main history in this UI, 
            # or could be displayed if desired. 
            # For brevity/cleanness, omitting simple rendering here or adding it.
            # If you want to see tool usage in history, add `elif isinstance(message, ToolMessage): ...`

        # Handle user input
        if prompt := st.chat_input("Type your message here..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                # Container for tool statuses - created FIRST so it appears above response
                status_container = st.status("Thinking...", expanded=True)
                
                # Message placeholder created AFTER status so response appears below
                message_placeholder = st.empty()
                full_response = ""
                
                async for msg, metadata in chatbot.astream(
                    {"messages": [HumanMessage(content=prompt)]}, 
                    config=config, 
                    stream_mode="messages"
                ):
                    if isinstance(msg, AIMessage):
                        if msg.tool_calls:
                            for tool in msg.tool_calls:
                                status_container.write(f"🛠️ Using tool: **{tool['name']}**")
                        
                        if msg.content:
                            full_response += msg.content
                            message_placeholder.markdown(full_response + "▌")
                    
                    elif isinstance(msg, ToolMessage):
                        status_container.write(f"✅ Tool result: **{msg.name}**")
                
                status_container.update(label="Complete", state="complete", expanded=False)
                
                message_placeholder.markdown(full_response)
                
                if not full_response:
                     message_placeholder.markdown("No response generated.")

if __name__ == "__main__":
    asyncio.run(main())
