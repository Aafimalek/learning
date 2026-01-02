# ========== chains.py ==========
from llm import llm
from prompt import create_prompt

def get_chat_chain():
    prompt = create_prompt()
    chain = prompt | llm
    return chain