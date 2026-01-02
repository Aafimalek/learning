from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()  # reads .env into system environment

api_key = os.getenv("GROQ_API_KEY")
print(api_key)

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.1,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
