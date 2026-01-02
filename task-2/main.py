import streamlit as st
import os
import json
import re
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage

from schema import AssistantResponse
from tools import tools

load_dotenv()

st.set_page_config(page_title="Decision Assistant", layout="centered")

# --- 1. MODEL CONFIGURATION ---
# llama-3.3-70b-versatile is the 2026 stable replacement for decommissioned Llama 3 models
SUPPORTED_MODEL = "llama-3.3-70b-versatile"

llm = ChatGroq(
    model=SUPPORTED_MODEL, 
    temperature=0, 
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# We'll use regular LLM calls and parse JSON manually for more reliability

# --- 2. OPTIMIZED PROMPT ---
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a highly capable Decision Assistant. 
    1. If the request requires live data or math, you MUST call the relevant tool. 
    2. Do NOT summarize or guess if a tool can find the answer. 
    3. Always think step-by-step before selecting a tool. 
    4. After using a tool, analyze the result and provide a clear, final answer to the user.
    5. Once you have the answer, STOP and provide it directly - do not call tools again.
    6. For math problems, use python_interpreter once to calculate, then provide the result.
    7. Ensure your tool arguments are valid JSON objects."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# --- 3. AGENT EXECUTION ---
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    max_iterations=15,
    early_stopping_method="force", # Use 'force' to stop safely without re-calling the LLM
    handle_parsing_errors=True,    # Recovers if the model misformats tool arguments
    return_intermediate_steps=True  # Helps with debugging and error handling
)

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    st.chat_message(role).write(msg.content)

# Handle Input
if user_input := st.chat_input("Ask a question..."):
    st.session_state.messages.append(HumanMessage(content=user_input))
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        # FIXED: Initialize callback handler inside the specific container to maintain UI thread sync
        st_container = st.container()
        st_callback = StreamlitCallbackHandler(st_container)
        
        try:
            # Step A: Invoke Agent with Callback
            response = agent_executor.invoke(
                {"input": user_input, "chat_history": st.session_state.messages},
                {"callbacks": [st_callback]}
            )
            
            # Check if we got a valid output
            agent_output = response.get('output', '').strip()
            
            if not agent_output:
                st.warning("Agent completed but did not produce an output. This may indicate it hit max iterations.")
                # Try to extract answer from intermediate steps
                intermediate_steps = response.get('intermediate_steps', [])
                if intermediate_steps:
                    last_step = intermediate_steps[-1]
                    if len(last_step) > 1:
                        tool_output = str(last_step[1])
                        agent_output = f"Based on tool execution: {tool_output}"
            
            # Step B: Final Structured Formatting
            # Structured output ensures consistency for professional internal workflows
            if agent_output:
                try:
                    # Extract tools used from intermediate steps
                    intermediate_steps = response.get('intermediate_steps', [])
                    tools_used_list = []
                    for step in intermediate_steps:
                        if len(step) > 0:
                            # Handle different step formats
                            action = step[0]
                            if hasattr(action, 'tool'):
                                tool_name = action.tool
                            elif hasattr(action, 'tool_name'):
                                tool_name = action.tool_name
                            elif isinstance(action, dict):
                                tool_name = action.get('tool') or action.get('tool_name')
                            else:
                                # Try to extract from string representation
                                tool_name = None
                                action_str = str(action)
                                for tool in [t.name for t in tools]:
                                    if tool in action_str:
                                        tool_name = tool
                                        break
                            
                            if tool_name and tool_name not in tools_used_list and tool_name in [t.name for t in tools]:
                                tools_used_list.append(tool_name)
                    
                    extraction_prompt = f"""Extract information from the agent response and return ONLY valid JSON (no markdown, no code blocks, just raw JSON).

Agent Response: {agent_output}

Tools Actually Used: {tools_used_list if tools_used_list else 'None'}

Return a JSON object with these exact fields:
{{
  "reasoning": "Step-by-step logic used to solve the query",
  "answer": "The final concise answer",
  "tools_used": {tools_used_list if tools_used_list else []},
  "confidence": 1.0
}}

CRITICAL TYPE REQUIREMENTS:
- "confidence" must be a NUMBER (1.0, 0.9, 0.8), NOT a string
- "tools_used" must be an ARRAY of strings like ["python_interpreter"], NOT a string
- Return ONLY the JSON object, nothing else"""
                    
                    try:
                        # Use regular LLM call and parse JSON manually
                        json_response = llm.invoke(extraction_prompt)
                        json_text = json_response.content.strip()
                        
                        # Remove markdown code blocks if present
                        if json_text.startswith("```"):
                            json_text = re.sub(r'^```(?:json)?\s*\n', '', json_text)
                            json_text = re.sub(r'\n```\s*$', '', json_text)
                        
                        # Parse JSON
                        parsed = json.loads(json_text)
                        
                        # Fix types and create response
                        confidence = parsed.get('confidence', 1.0)
                        if isinstance(confidence, str):
                            try:
                                confidence = float(confidence)
                            except:
                                confidence = 1.0
                        
                        tools_used = parsed.get('tools_used', [])
                        if isinstance(tools_used, str):
                            try:
                                tools_used = json.loads(tools_used) if tools_used.startswith('[') else [tools_used] if tools_used else []
                            except:
                                tools_used = [tools_used] if tools_used else []
                        
                        # Use extracted tools if available
                        if tools_used_list:
                            tools_used = tools_used_list
                        
                        final_data = AssistantResponse(
                            reasoning=parsed.get('reasoning', 'Processed the query step by step.'),
                            answer=parsed.get('answer', agent_output),
                            tools_used=tools_used if isinstance(tools_used, list) else [],
                            confidence=float(confidence)
                        )
                    except json.JSONDecodeError as json_error:
                        # If JSON parsing fails, try to extract JSON from the response
                        json_text = json_response.content if 'json_response' in locals() else str(json_error)
                        json_match = re.search(r'\{[^{}]*"reasoning"[^{}]*"answer"[^{}]*"tools_used"[^{}]*"confidence"[^{}]*\}', json_text, re.DOTALL)
                        if json_match:
                            try:
                                parsed = json.loads(json_match.group(0))
                                final_data = AssistantResponse(
                                    reasoning=parsed.get('reasoning', 'Processed the query.'),
                                    answer=parsed.get('answer', agent_output),
                                    tools_used=tools_used_list if tools_used_list else (parsed.get('tools_used', []) if isinstance(parsed.get('tools_used'), list) else []),
                                    confidence=float(parsed.get('confidence', 1.0)) if isinstance(parsed.get('confidence'), (int, float)) else 1.0
                                )
                            except:
                                # Final fallback
                                final_data = AssistantResponse(
                                    reasoning=f"Processed the query: {agent_output[:200]}",
                                    answer=agent_output.split('.')[0] if '.' in agent_output else agent_output[:100],
                                    tools_used=tools_used_list,
                                    confidence=1.0 if tools_used_list else 0.8
                                )
                        else:
                            # Final fallback: create response from agent output
                            final_data = AssistantResponse(
                                reasoning=f"Processed the query using available tools.",
                                answer=agent_output.split('.')[0] if '.' in agent_output else agent_output[:100],
                                tools_used=tools_used_list,
                                confidence=1.0 if tools_used_list else 0.8
                            )
                    except Exception as parse_error:
                        # Fallback: create response from agent output
                        final_data = AssistantResponse(
                            reasoning=f"Processed the query: {agent_output[:200]}",
                            answer=agent_output.split('.')[0] if '.' in agent_output else agent_output[:100],
                            tools_used=tools_used_list,
                            confidence=1.0 if tools_used_list else 0.8
                        )
                    
                    # Final validation to ensure types are correct
                    final_data.confidence = float(final_data.confidence) if isinstance(final_data.confidence, (int, float)) else 1.0
                    if not isinstance(final_data.tools_used, list):
                        final_data.tools_used = tools_used_list if tools_used_list else []
                    elif tools_used_list:
                        # Override with actual extracted tools
                        final_data.tools_used = tools_used_list
                    
                    # Step C: Render Output
                    st.markdown(f"### {final_data.answer}")
                    with st.expander("🔍 Decision Logic"):
                        st.write(f"**Tools Used:** {', '.join(final_data.tools_used) if final_data.tools_used else 'None'}")
                        st.info(final_data.reasoning)
                    
                    st.session_state.messages.append(AIMessage(content=final_data.answer))
                except Exception as struct_error:
                    # Fallback: display raw output if structured extraction fails
                    st.markdown(f"### Answer")
                    st.write(agent_output)
                    st.session_state.messages.append(AIMessage(content=agent_output))
                    st.warning(f"Structured extraction failed: {str(struct_error)}")
            else:
                st.error("Unable to generate a response. The agent may have encountered an issue.")
                st.info("Tip: Try rephrasing your query or check if the tools are working correctly.")

        except Exception as e:
            st.error(f"Execution Error: {str(e)}")
            st.info("Tip: This can happen if search results are too large or the logic loops. Try a specific query.")