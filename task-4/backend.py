from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.message import add_messages
import os
import json
import hashlib
import shutil
from dotenv import load_dotenv
import aiosqlite
import httpx
import tempfile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
import chromadb

load_dotenv()
os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1)

# Module-level variable to track current thread for RAG
_current_thread_id: str | None = None

def set_current_thread(thread_id: str):
    """Set the current thread ID for RAG tool access and load its retriever if exists."""
    global _current_thread_id
    _current_thread_id = thread_id
    # Try to load existing retriever for this thread
    _load_retriever_for_thread(thread_id)

# -------------------
# 1. Embeddings & Logic
# -------------------
# Ensure Ollama is running at this URL or configured appropriately
embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://127.0.0.1:11434")

# -------------------
# 2. Persistent Storage Setup
# -------------------
CHROMA_PERSIST_DIR = "chroma_db"
DOCUMENTS_DIR = "uploaded_documents"
METADATA_FILE = "chroma_metadata.json"
DOC_HASH_FILE = "document_hashes.json"  # Maps file hash -> collection name

# Create directories if they don't exist
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Create persistent Chroma client
_chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# In-memory cache for retrievers (loaded from persistent storage)
_THREAD_RETRIEVERS: dict[str, object] = {}
_THREAD_METADATA: dict[str, dict] = {}

def _load_metadata() -> dict:
    """Load metadata from JSON file."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_metadata(metadata: dict):
    """Save metadata to JSON file."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def _load_doc_hashes() -> dict:
    """Load document hash mappings from JSON file."""
    if os.path.exists(DOC_HASH_FILE):
        try:
            with open(DOC_HASH_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_doc_hashes(hashes: dict):
    """Save document hash mappings to JSON file."""
    with open(DOC_HASH_FILE, 'w') as f:
        json.dump(hashes, f, indent=2)

def _compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA256 hash of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()

def _get_collection_name_for_hash(file_hash: str) -> str:
    """Generate a collection name based on file hash."""
    return f"doc_{file_hash[:16]}"

def _get_collection_name(thread_id: str) -> str:
    """Generate a valid collection name for a thread."""
    # Chroma collection names must be 3-63 chars, alphanumeric with underscores/hyphens
    return f"thread_{thread_id.replace('-', '_')}"

def _load_retriever_for_thread(thread_id: str):
    """Load an existing retriever from persistent Chroma for a thread."""
    global _THREAD_RETRIEVERS, _THREAD_METADATA
    
    if thread_id in _THREAD_RETRIEVERS:
        return  # Already loaded
    
    # First, check metadata to get the correct collection name
    all_metadata = _load_metadata()
    
    if thread_id not in all_metadata:
        return  # No document for this thread
    
    thread_meta = all_metadata[thread_id]
    _THREAD_METADATA[thread_id] = thread_meta
    
    # Get collection name from metadata (new style) or fall back to thread-based name (old style)
    collection_name = thread_meta.get("collection_name", _get_collection_name(thread_id))
    
    try:
        # Check if collection exists
        existing_collections = [c.name for c in _chroma_client.list_collections()]
        if collection_name in existing_collections:
            # Load existing collection
            vector_store = Chroma(
                client=_chroma_client,
                collection_name=collection_name,
                embedding_function=embeddings
            )
            
            # Verify it has documents
            collection = _chroma_client.get_collection(collection_name)
            if collection.count() > 0:
                retriever = vector_store.as_retriever(
                    search_type="similarity", search_kwargs={"k": 4}
                )
                _THREAD_RETRIEVERS[thread_id] = retriever
    except Exception as e:
        print(f"Error loading retriever for thread {thread_id}: {e}")

def get_thread_pdf_info(thread_id: str) -> dict | None:
    """Get PDF metadata for a thread if it has an uploaded document."""
    # First check in-memory cache
    if thread_id in _THREAD_METADATA:
        return _THREAD_METADATA[thread_id]
    
    # Otherwise check persistent metadata
    all_metadata = _load_metadata()
    if thread_id in all_metadata:
        _THREAD_METADATA[thread_id] = all_metadata[thread_id]
        return all_metadata[thread_id]
    
    return None

def _get_retriever(thread_id: str | None):
    """Fetch the retriever for a thread if available."""
    if thread_id:
        # Try to load if not in cache
        if thread_id not in _THREAD_RETRIEVERS:
            _load_retriever_for_thread(thread_id)
        return _THREAD_RETRIEVERS.get(thread_id)
    return None

def _save_document(file_bytes: bytes, filename: str, file_hash: str) -> str:
    """Save document to the documents folder and return the path."""
    # Create a subfolder for each document hash to avoid name collisions
    doc_folder = os.path.join(DOCUMENTS_DIR, file_hash[:16])
    os.makedirs(doc_folder, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(doc_folder, filename)
    with open(file_path, 'wb') as f:
        f.write(file_bytes)
    
    return file_path

def _get_or_create_collection_for_document(file_bytes: bytes, filename: str) -> tuple[str, dict, bool]:
    """
    Check if document already exists (by hash). If so, return existing collection name.
    Otherwise, create new collection and return it.
    Returns: (collection_name, metadata, was_cached)
    """
    file_hash = _compute_file_hash(file_bytes)
    collection_name = _get_collection_name_for_hash(file_hash)
    
    # Check if this document was already processed
    doc_hashes = _load_doc_hashes()
    
    if file_hash in doc_hashes:
        # Document already exists, check if collection is valid
        existing_info = doc_hashes[file_hash]
        try:
            existing_collections = [c.name for c in _chroma_client.list_collections()]
            if collection_name in existing_collections:
                collection = _chroma_client.get_collection(collection_name)
                if collection.count() > 0:
                    # Valid cached document
                    return collection_name, existing_info, True
        except:
            pass
    
    # Need to process the document
    # Save the document to disk
    saved_path = _save_document(file_bytes, filename, file_hash)
    
    # Load and process the PDF
    loader = PDFPlumberLoader(saved_path)
    docs = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(docs)
    
    # Delete existing collection if it exists (for re-processing)
    try:
        existing_collections = [c.name for c in _chroma_client.list_collections()]
        if collection_name in existing_collections:
            _chroma_client.delete_collection(collection_name)
    except:
        pass
    
    # Create persistent Chroma vector store
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=_chroma_client,
        collection_name=collection_name
    )
    
    # Save document info
    metadata = {
        "filename": filename,
        "documents": len(docs),
        "chunks": len(chunks),
        "file_hash": file_hash,
        "saved_path": saved_path,
        "collection_name": collection_name
    }
    
    # Update hash mapping
    doc_hashes[file_hash] = metadata
    _save_doc_hashes(doc_hashes)
    
    return collection_name, metadata, False

def ingest_pdf(file_bytes: bytes, thread_id: str, filename: str | None = None) -> dict:
    """
    Build a persistent Chroma retriever for the uploaded PDF and store it for the thread.
    Uses caching - if the same document was uploaded before, reuses the existing embeddings.
    """
    if not file_bytes:
        raise ValueError("No bytes received for ingestion.")
    
    actual_filename = filename or "uploaded.pdf"
    
    # Get or create collection for this document (with caching)
    collection_name, doc_info, was_cached = _get_or_create_collection_for_document(
        file_bytes, actual_filename
    )
    
    # Load the vector store and create retriever
    vector_store = Chroma(
        client=_chroma_client,
        collection_name=collection_name,
        embedding_function=embeddings
    )
    
    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": 4}
    )
    
    _THREAD_RETRIEVERS[str(thread_id)] = retriever
    
    # Save metadata for this thread (linking to the document)
    thread_metadata = {
        "filename": doc_info["filename"],
        "documents": doc_info["documents"],
        "chunks": doc_info["chunks"],
        "file_hash": doc_info["file_hash"],
        "collection_name": collection_name,
        "cached": was_cached
    }
    _THREAD_METADATA[str(thread_id)] = thread_metadata
    
    # Persist thread metadata
    all_metadata = _load_metadata()
    all_metadata[str(thread_id)] = thread_metadata
    _save_metadata(all_metadata)
    
    return {
        **thread_metadata,
        "message": "Using cached embeddings" if was_cached else "Processed new document"
    }

# Tools
@tool
def web_search(query: str) -> str:
    """
    Search the internet for current events, news, general knowledge, or any real-world information.
    Use this tool when the user asks about:
    - Current events or news
    - General facts or information
    - Questions about real-world topics
    - Anything NOT related to an uploaded PDF document
    
    Args:
        query: The search query string.
    """
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No results found."
            return "\n\n".join([f"Title: {r['title']}\nSnippet: {r['body']}" for r in results])
    except Exception as e:
        return f"Search failed: {str(e)}"

@tool
def document_search(query: str) -> str:
    """
    Search the uploaded PDF document for relevant information.
    Use this tool when the user:
    - Asks questions about "the document", "the PDF", "the file", or "the uploaded file"
    - Wants information from their uploaded document
    - References content they uploaded
    - Asks "what does the document say about..."
    DO NOT use this for general web searches or questions unrelated to uploaded documents.
    
    Args:
        query: The question or search terms to find in the document.
    """
    global _current_thread_id
    try:
        if not _current_thread_id:
            return "No active session. Please try again."
            
        retriever = _get_retriever(_current_thread_id)
        if retriever is None:
            return "No document has been uploaded yet. Please upload a PDF first."

        results = retriever.invoke(query)
        if not results:
            return "No relevant information found in the document."
            
        context = "\n\n---\n\n".join([doc.page_content for doc in results])
        filename = _THREAD_METADATA.get(str(_current_thread_id), {}).get("filename", "unknown")
        return f"From document '{filename}':\n\n{context}"
    except Exception as e:
        return f"Document search failed: {str(e)}"

@tool
def calculator(expression: str) -> str:
    """
    Calculate a mathematical expression. Use this tool when the user:
    - Asks to calculate, compute, or solve a math problem
    - Needs arithmetic operations (+, -, *, /)
    - Wants to evaluate a numerical expression
    
    Args:
        expression: A math expression like "2 + 3 * 4" or "(10 - 5) / 2"
    """
    try:
        # Safe evaluation of math expressions
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Invalid expression. Only numbers and +, -, *, /, () are allowed."
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculation error: {str(e)}"

@tool
def get_stock_price(symbol: str) -> str:
    """
    Get the current stock price for a company. Use this tool when the user:
    - Asks about stock prices
    - Wants to know the price of a stock like Apple, Tesla, Google, Microsoft, etc.
    - Mentions ticker symbols like AAPL, TSLA, GOOGL, MSFT
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL" for Apple, "TSLA" for Tesla)
    """
    try:
        import requests
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
        r = requests.get(url, timeout=10)
        data = r.json()
        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            price = quote.get("05. price", "N/A")
            change = quote.get("10. change percent", "N/A")
            return f"{symbol}: ${price} ({change})"
        return f"Could not find stock data for {symbol}"
    except Exception as e:
        return f"Stock lookup failed: {str(e)}"

# Simple tool list with string returns
tools = [web_search, calculator, get_stock_price, document_search]
llm_with_tools = llm.bind_tools(tools)

# System prompt to guide tool usage
SYSTEM_PROMPT = """You are a helpful AI assistant with access to the following tools:
- web_search: Search the internet for current events, news, or general information
- calculator: Perform mathematical calculations
- get_stock_price: Get current stock prices for companies
- document_search: Search uploaded PDF documents for information

Choose the appropriate tool based on the user's question. If no tool is needed, respond directly.
For document questions, ONLY use document_search if the user has uploaded a PDF and is asking about it."""


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


async def chat_node(state: ChatState):
    from langchain_core.messages import SystemMessage
    
    # take user query from state
    messages = state['messages']
    
    # Prepend system message if not already present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    # send to llm
    response = await llm_with_tools.ainvoke(messages)

    # response store state
    return {'messages': [response]}


async def get_thread_ids(db_path="checkpoints.db"):
    try:
        async with aiosqlite.connect(db_path) as db:
            # Check if table exists first to avoid error on fresh start
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints';") as cursor:
                 if await cursor.fetchone() is None:
                    return []
            
            async with db.execute("SELECT DISTINCT thread_id FROM checkpoints") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    except Exception as e:
        print(f"Error fetching threads: {e}")
        return []

async def delete_thread(thread_id: str, db_path="checkpoints.db"):
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            await db.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            await db.commit()
        
        # Also delete Chroma collection for this thread
        collection_name = _get_collection_name(thread_id)
        try:
            existing_collections = [c.name for c in _chroma_client.list_collections()]
            if collection_name in existing_collections:
                _chroma_client.delete_collection(collection_name)
        except Exception as e:
            print(f"Error deleting Chroma collection: {e}")
        
        # Remove from in-memory cache
        if thread_id in _THREAD_RETRIEVERS:
            del _THREAD_RETRIEVERS[thread_id]
        if thread_id in _THREAD_METADATA:
            del _THREAD_METADATA[thread_id]
        
        # Update metadata file
        all_metadata = _load_metadata()
        if thread_id in all_metadata:
            del all_metadata[thread_id]
            _save_metadata(all_metadata)
        
        return True
    except Exception as e:
        print(f"Error deleting thread {thread_id}: {e}")
        return False


graph = StateGraph(ChatState)

# add nodes
graph.add_node('chat_node', chat_node)
graph.add_node('tools', ToolNode(tools))

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')

# Export graph only, compile in app with async checkpointer

