from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver 
from langgraph.graph.message import add_messages
import os
from dotenv import load_dotenv

load_dotenv()
os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.5)


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]



def chat_node(state: ChatState):

    # take user query from state
    messages = state['messages']

    # send to llm
    # Use stream and aggregate to enable streaming events
    # We need to construct the final message manually if we just consume text,
    # but llm.stream yields chunks we can add.
    response = None
    for chunk in llm.stream(messages):
        if response is None:
            response = chunk
        else:
            response += chunk

    # response store state
    return {'messages': [response]}

checkpointer= InMemorySaver()

# Store thread IDs
thread_ids = []

def add_thread_id(thread_id: str):
    if thread_id not in thread_ids:
        thread_ids.append(thread_id)

def get_thread_ids():
    return thread_ids


graph = StateGraph(ChatState)

# add nodes
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)
