# 🤖 GenAI & Agentic AI Learning Repository

<div align="center">

![GenAI Banner](https://img.shields.io/badge/GenAI-Learning%20Journey-blue?style=for-the-badge&logo=openai)
![LangChain](https://img.shields.io/badge/LangChain-Framework-green?style=for-the-badge)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20AI-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)

**A comprehensive learning repository documenting my journey through Generative AI and Agentic AI concepts**

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Repository Structure](#-repository-structure)
- [Learning Progress](#-learning-progress)
- [Task-1: LangChain Chat Basics](#-task-1-langchain-chat-basics)
- [Task-2: Tool-Calling Agents](#-task-2-tool-calling-agents)
- [Task-3: Multi-Stage Pipeline (Legal Case Analysis)](#-task-3-multi-stage-pipeline-legal-case-analysis)
- [Task-4: LangGraph & Advanced Agentic AI](#-task-4-langgraph--advanced-agentic-ai)
- [Key Concepts Reference](#-key-concepts-reference)
- [How to Add New Tasks](#-how-to-add-new-tasks)
- [Setup & Installation](#-setup--installation)
- [Resources](#-resources)

---

## 🎯 Overview

This repository serves as my personal **learning logbook** for Generative AI (GenAI) and Agentic AI. It contains progressively complex implementations, starting from basic chatbots to sophisticated multi-agent systems with long-term memory.

### 🧠 Core Technologies Covered

| Technology | Description | Tasks Used In |
|------------|-------------|---------------|
| **LangChain** | Framework for LLM application development | Task 1, 2, 3, 4 |
| **LangGraph** | Framework for building agentic workflows | Task 4 |
| **Groq API** | High-speed LLM inference (Llama, Qwen models) | All Tasks |
| **Streamlit** | Web UI framework for ML applications | Task 1, 2, 3, 4 |
| **ChromaDB** | Vector database for embeddings | Task 4 |
| **Pydantic** | Data validation & structured outputs | All Tasks |

---

## 📁 Repository Structure

```
training/
├── README.md                    # This file - Learning logbook
├── task-1/                      # LangChain Chat Basics
│   ├── app.py                   # Streamlit chat interface
│   ├── chains.py                # LangChain chain composition
│   ├── llm.py                   # LLM configuration (Groq)
│   ├── prompt.py                # Prompt templates
│   └── requirements.txt
├── task-2/                      # Tool-Calling Agents
│   ├── main.py                  # Agentic assistant with tools
│   ├── tools.py                 # Tool definitions (search, calculator, etc.)
│   ├── schema.py                # Pydantic response schemas
│   └── requirements.txt
├── task-3/                      # Multi-Stage Legal Analysis Pipeline
│   ├── app.py                   # Main Streamlit application
│   ├── pipeline.py              # 5-stage analysis pipeline
│   ├── memory.py                # Session state management
│   ├── llm.py                   # LLM configuration
│   ├── config.py                # Application configuration
│   ├── schemas.py               # Pydantic schemas for all stages
│   ├── prompts/                 # Prompt templates per stage
│   │   ├── understand_case.txt
│   │   ├── extract_facts.txt
│   │   ├── identify_issues.txt
│   │   ├── generate_arguments.txt
│   │   └── predict_judgement.txt
│   ├── qna/                     # Q&A system with context builder
│   │   ├── context_builder.py
│   │   ├── qna_engine.py
│   │   ├── qna_memory.py
│   │   └── qna_prompts.txt
│   └── requirements.txt
├── task-4/                      # LangGraph Advanced Concepts
│   ├── app.py                   # RAG-enabled chatbot UI
│   ├── backend.py               # LangGraph state machine + tools
│   ├── hitl_example.py          # Human-in-the-Loop demo
│   ├── langgraph_essay.py       # Parallel evaluation workflow
│   ├── langgraph_chatbot.ipynb  # Basic LangGraph tutorial
│   ├── ltm_basics.ipynb         # Long-Term Memory basics
│   ├── ltm_advance.ipynb        # Advanced LTM patterns
│   ├── chroma_db/               # Persistent vector storage
│   ├── uploaded_documents/      # PDF storage for RAG
│   └── requirements.txt
└── .env                         # API keys (not tracked)
```

---

## 📊 Learning Progress

| Task | Topic | Complexity | Status |
|------|-------|------------|--------|
| Task 1 | LangChain Chat Basics | ⭐ Beginner | ✅ Complete |
| Task 2 | Tool-Calling Agents | ⭐⭐ Intermediate | ✅ Complete |
| Task 3 | Multi-Stage Pipelines | ⭐⭐⭐ Advanced | ✅ Complete |
| Task 4 | LangGraph & Long-Term Memory | ⭐⭐⭐⭐ Expert | ✅ Complete |
| Task 5 | *Future* | - | 🔜 Planned |

---

## 📘 Task-1: LangChain Chat Basics

### 🎯 Learning Objectives
- Understand LangChain fundamentals
- Build a basic chatbot with conversation history
- Learn prompt templating with `ChatPromptTemplate`
- Use `MessagesPlaceholder` for dynamic chat history

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                          │
│                      (app.py)                            │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   LangChain Chain                        │
│                    (chains.py)                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Prompt    │ -> │     LLM     │ -> │   Output    │  │
│  │  Template   │    │   (Groq)    │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 📝 Key Code Patterns

#### 1. Chain Composition (LCEL - LangChain Expression Language)
```python
# chains.py - Simple chain using pipe operator
def get_chat_chain():
    prompt = create_prompt()
    chain = prompt | llm  # LCEL: prompt pipes into LLM
    return chain
```

#### 2. Prompt Template with Chat History
```python
# prompt.py - Using MessagesPlaceholder for conversation memory
def create_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant..."),
        MessagesPlaceholder(variable_name="chat_history"),  # Dynamic history
        ("human", "{input}")
    ])
```

#### 3. Session State Management
```python
# app.py - Streamlit session state for persistence
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Storing messages as LangChain message objects
st.session_state.chat_history.append(HumanMessage(content=user_input))
st.session_state.chat_history.append(AIMessage(content=bot_reply))
```

### 📊 Concept Diagram: Chat History Flow

```
User Input ─────────────────────────────────────────────────────────┐
     │                                                               │
     ▼                                                               │
┌─────────────────────────────────────────────────────────────┐      │
│                    ChatPromptTemplate                        │      │
│  ┌─────────────────────────────────────────────────────────┐│      │
│  │ System: "You are a helpful assistant..."                 ││      │
│  ├─────────────────────────────────────────────────────────┤│      │
│  │ MessagesPlaceholder (chat_history)                       ││◄─────┘
│  │   - HumanMessage: "What is AI?"                          ││   Previous
│  │   - AIMessage: "AI stands for..."                        ││   Messages
│  │   - HumanMessage: "Tell me more"                         ││
│  │   - AIMessage: "Sure, AI can..."                         ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ Human: "{input}" ◄─── Current User Input                 ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Groq LLM   │
                   │  (Qwen 32B) │
                   └──────┬──────┘
                          │
                          ▼
                    AI Response
```

### 🔧 Technologies Used
- **LangChain Core**: `ChatPromptTemplate`, `MessagesPlaceholder`
- **LangChain Groq**: `ChatGroq` for LLM inference
- **Model**: `qwen/qwen3-32b` (via Groq)
- **UI**: Streamlit

---

## 🛠️ Task-2: Tool-Calling Agents

### 🎯 Learning Objectives
- Understand the **ReAct (Reasoning + Acting)** pattern
- Build an agent that can use external tools
- Learn tool definition with schemas
- Implement structured output parsing
- Handle agent iterations and error recovery

### 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                       Streamlit UI                              │
└───────────────────────────────┬────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────┐
│                      AgentExecutor                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    ReAct Loop                             │  │
│  │                                                           │  │
│  │   ┌─────────┐    ┌────────────┐    ┌─────────────────┐   │  │
│  │   │ Thought │ -> │   Action   │ -> │   Observation   │   │  │
│  │   │         │    │ (Tool Call)│    │ (Tool Result)   │   │  │
│  │   └────┬────┘    └─────┬──────┘    └────────┬────────┘   │  │
│  │        │               │                     │            │  │
│  │        └───────────────┴─────────────────────┘            │  │
│  │                        │                                   │  │
│  │                        ▼                                   │  │
│  │              Final Answer or Repeat                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────┐
│                        Tool Suite                               │
│  ┌──────────────┐  ┌────────────┐  ┌────────────────────────┐  │
│  │ DuckDuckGo   │  │ Wikipedia  │  │ Python Interpreter     │  │
│  │   Search     │  │   Query    │  │    (Calculator)        │  │
│  └──────────────┘  └────────────┘  └────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 📝 Key Code Patterns

#### 1. Tool Definition with Pydantic Schema
```python
# tools.py - Defining tools with input validation
class PythonInterpreterInput(BaseModel):
    """Input schema for python interpreter tool."""
    code: str = Field(description="The Python code to execute.")

tools = [
    Tool(
        name="duckduckgo_search",
        func=DuckDuckGoSearchRun().run,
        description="Search the live web for current events..."
    ),
    StructuredTool(
        name="python_interpreter",
        func=python_interpreter_wrapper,
        description="Execute python code for complex math...",
        args_schema=PythonInterpreterInput  # Pydantic validation
    )
]
```

#### 2. Agent Creation with Tool Binding
```python
# main.py - Creating tool-calling agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    max_iterations=15,
    early_stopping_method="force",
    handle_parsing_errors=True,
    return_intermediate_steps=True
)
```

#### 3. Structured Response Schema
```python
# schema.py - Enforcing output structure
class AssistantResponse(BaseModel):
    """The final validated output for the user."""
    reasoning: str = Field(description="Step-by-step logic used...")
    answer: str = Field(description="The final concise answer...")
    tools_used: List[str] = Field(description="List of tools accessed...")
    confidence: float = Field(description="Confidence score 0-1")
```

### 📊 ReAct Pattern Visualization

```
User Query: "What is 2^100 + the current price of Apple stock?"
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      ITERATION 1                             │
│  Thought: I need to calculate 2^100 first                    │
│  Action: python_interpreter                                  │
│  Action Input: {"code": "print(2**100)"}                     │
│  Observation: 1267650600228229401496703205376                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      ITERATION 2                             │
│  Thought: Now I need current Apple stock price               │
│  Action: duckduckgo_search                                   │
│  Action Input: "current Apple AAPL stock price"              │
│  Observation: Apple (AAPL) is trading at $187.50...          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      ITERATION 3                             │
│  Thought: I have both values, can now answer                 │
│  Final Answer: 2^100 = 1.27×10^30. Apple stock is $187.50.  │
│                The sum is approximately 1.27×10^30          │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 Technologies Used
- **LangChain Classic**: `AgentExecutor`, `create_tool_calling_agent`
- **Tools**: DuckDuckGoSearch, WikipediaQuery, PythonREPL
- **Model**: `llama-3.3-70b-versatile` (via Groq)
- **Callbacks**: `StreamlitCallbackHandler` for real-time UI updates

---

## ⚖️ Task-3: Multi-Stage Pipeline (Legal Case Analysis)

### 🎯 Learning Objectives
- Build a **multi-stage LLM pipeline** where outputs flow between stages
- Implement **structured JSON output** with repair mechanisms
- Create a **context-aware Q&A system** over analysis results
- Learn memory management for both pipeline state and conversations
- Design **modular prompt engineering** with external template files

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Streamlit UI (app.py)                        │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    5-STAGE ANALYSIS PIPELINE                         │
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│  │  Stage 1    │    │  Stage 2    │    │       Stage 3           │  │
│  │ Understand  │───>│  Extract    │───>│   Identify Issues       │  │
│  │    Case     │    │   Facts     │    │   (+ Follow-up Q)       │  │
│  └─────────────┘    └─────────────┘    └───────────┬─────────────┘  │
│                                                     │                │
│                                                     ▼                │
│  ┌─────────────────────────────────┐    ┌─────────────────────────┐  │
│  │          Stage 5                │    │       Stage 4           │  │
│  │    Predict Judgment             │◄───│   Generate Arguments    │  │
│  │   (outcome + confidence)        │    │   (both sides)          │  │
│  └─────────────────────────────────┘    └─────────────────────────┘  │
│                      │                                               │
└──────────────────────┼───────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Q&A SYSTEM (qna/)                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Context Builder  │->│   QnA Engine     │->│   QnA Memory     │   │
│  │ (keyword-based)  │  │ (answer from     │  │ (conversation    │   │
│  │                  │  │  context only)   │  │  history)        │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 📊 Pipeline Stage Details

| Stage | Input | Output | Prompt File | Purpose |
|-------|-------|--------|-------------|---------|
| **1. Understand Case** | Raw case text | Summary, parties, timeline, ambiguities | `understand_case.txt` | Paraphrase without legal conclusions |
| **2. Extract Facts** | Understanding | Material facts, procedural facts, evidence | `extract_facts.txt` | Separate facts from interpretation |
| **3. Identify Issues** | Facts + Follow-up | List of legal questions | `identify_issues.txt` | Spot legal issues as questions |
| **4. Generate Arguments** | Facts + Issues | Arguments for both sides per issue | `generate_arguments.txt` | Balanced argument generation |
| **5. Predict Judgment** | Facts + Issues + Arguments | Outcome, reasoning, confidence | `predict_judgement.txt` | Cautious prediction with assumptions |

### 📝 Key Code Patterns

#### 1. JSON Output Extraction with Repair
```python
# pipeline.py - Robust JSON parsing from LLM output
def repair_json(json_text: str) -> str:
    """Fix common LLM JSON issues like missing commas."""
    # Fix missing commas after closing brackets
    json_text = re.sub(r'([\]}])\s*\n\s*(")', r'\1,\n\2', json_text)
    # Remove trailing commas (invalid JSON)
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    return json_text

def extract_json_from_text(text: str) -> str:
    """Extract JSON from markdown code blocks or raw text."""
    # Handle ```json ... ``` blocks
    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1)
    # ... balanced brace matching fallback
```

#### 2. Context-Aware Q&A Builder
```python
# qna/context_builder.py - Keyword-based context selection
ARGUMENT_KEYWORDS = {
    "argument", "arguments", "claim", "defense",
    "plaintiff", "defendant", "prosecution"
}

def build_context(question: str, analysis_memory: Dict) -> Dict:
    """Build minimal context based on question keywords."""
    question_lower = question.lower()
    context = {}
    
    # Include relevant sections based on keywords
    if any(word in question_lower for word in ARGUMENT_KEYWORDS):
        context["arguments"] = analysis_memory.get("arguments")
    
    return context
```

#### 3. Pydantic Schemas for Each Stage
```python
# schemas.py - Type-safe output structures
class CaseUnderstanding(BaseModel):
    summary: str = Field(..., description="Plain-language summary")
    parties: List[str] = Field(..., description="Parties involved")
    timeline: List[str] = Field(..., description="Chronological events")
    ambiguities: List[str] = Field(..., description="Unclear facts")

class IssueArguments(BaseModel):
    side_a: ArgumentSide = Field(..., description="Plaintiff arguments")
    side_b: ArgumentSide = Field(..., description="Defendant arguments")
    strength: Literal["weak", "moderate", "strong"]
```

### 📊 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                     RAW CASE TEXT (User Input)                        │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STAGE 1: understand_case.txt                                          │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Output: {                                                         │ │
│ │   "summary": "A contracted B for software development...",        │ │
│ │   "parties": ["Company A (Plaintiff)", "Developer B (Defendant)"],│ │
│ │   "timeline": ["Jan 2024: Contract signed", "Mar: Dispute arose"],│ │
│ │   "ambiguities": ["Payment terms unclear", "Scope not defined"]   │ │
│ │ }                                                                  │ │
│ └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STAGE 2: extract_facts.txt                                            │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Output: {                                                         │ │
│ │   "material_facts": ["Contract worth $50,000", "Deadline missed"],│ │
│ │   "procedural_facts": ["Filed in District Court"],                │ │
│ │   "evidence": ["Email exchanges", "Contract document"]            │ │
│ │ }                                                                  │ │
│ └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
                         [Stages 3, 4, 5...]
```

### 🔧 Technologies Used
- **Prompt Management**: External `.txt` template files
- **JSON Repair**: Custom regex-based repair utilities
- **Memory**: Streamlit session state for pipeline + Q&A
- **Model**: `moonshotai/kimi-k2-instruct-0905` (via Groq)

---

## 🔄 Task-4: LangGraph & Advanced Agentic AI

### 🎯 Learning Objectives
- Master **LangGraph** for stateful, multi-node agentic workflows
- Implement **checkpointing** for conversation persistence
- Build **Human-in-the-Loop (HITL)** systems with `interrupt()`
- Create **RAG pipelines** with ChromaDB vector storage
- Understand **Long-Term Memory (LTM)** patterns with InMemoryStore
- Learn **parallel node execution** for fan-out workflows

### 📁 Task-4 Components Overview

| File | Purpose | Key Concepts |
|------|---------|--------------|
| `langgraph_chatbot.ipynb` | Basic LangGraph intro | StateGraph, MemorySaver, checkpointing |
| `ltm_basics.ipynb` | Long-Term Memory fundamentals | InMemoryStore, namespaces, semantic search |
| `ltm_advance.ipynb` | Advanced LTM patterns | Memory extraction, deduplication, merged workflow |
| `langgraph_essay.py` | Parallel evaluation workflow | Fan-out pattern, score aggregation |
| `hitl_example.py` | Human-in-the-Loop demo | `interrupt()`, `Command(resume=...)` |
| `app.py` + `backend.py` | Full RAG chatbot | PDF ingestion, tool selection, async checkpointing |

---

### 📘 4.1 LangGraph Basics (langgraph_chatbot.ipynb)

#### Core Concepts

```python
# State definition with message accumulation
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # Auto-append messages

# Graph construction
graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

# Compile with memory
checkpointer = MemorySaver()
chatbot = graph.compile(checkpointer=checkpointer)
```

#### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                      │
│                                                              │
│    ┌───────┐         ┌────────────┐         ┌───────┐       │
│    │ START │────────>│ chat_node  │────────>│  END  │       │
│    └───────┘         └────────────┘         └───────┘       │
│                            │                                 │
│                            │ invoke LLM                      │
│                            ▼                                 │
│                    ┌────────────────┐                        │
│                    │   ChatState    │                        │
│                    │  {messages: []}│                        │
│                    └────────────────┘                        │
│                                                              │
│    ┌────────────────────────────────────────────────────┐   │
│    │              MemorySaver (Checkpointer)             │   │
│    │  thread_id: "1" -> {messages: [HumanMsg, AIMsg...]} │   │
│    └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

### 📗 4.2 Long-Term Memory Basics (ltm_basics.ipynb)

#### InMemoryStore Operations

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# Namespace = hierarchical key structure
namespace = ("user", "u1")  # Tuple representing path

# CRUD Operations
store.put(namespace, "1", {"data": "User likes pizza"})     # Create
store.get(namespace, "1")                                    # Read
store.search(namespace)                                      # List all
store.search(namespace, query="what does user like", limit=3) # Semantic search
```

#### Memory Namespace Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     InMemoryStore                            │
│                                                              │
│  Namespace: ("user", "u1")                                   │
│  ├── Key "1": {"data": "User likes pizza"}                   │
│  ├── Key "2": {"data": "User prefers dark mode"}             │
│  └── Key "3": {"data": "User is learning ML"}                │
│                                                              │
│  Namespace: ("user", "u2")                                   │
│  ├── Key "1": {"data": "User likes pasta"}                   │
│  └── Key "2": {"data": "User prefers light mode"}            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │        Semantic Search (with embeddings)               │  │
│  │  Query: "what are user's preferences"                  │  │
│  │  Results: ["prefers dark mode", "likes pizza"]         │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### 📙 4.3 Advanced Long-Term Memory (ltm_advance.ipynb)

#### Three Patterns Implemented

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Read-Only LTM** | Load pre-seeded memories, personalize responses | Known user profiles |
| **Write-Only LTM** | Extract and store memories from conversations | Learning preferences |
| **Merged Workflow** | Remember node → Chat node (both read and write) | Full personalization |

#### Memory Extraction with Deduplication

```python
# Schema for memory decisions
class MemoryItem(BaseModel):
    text: str = Field(description="Atomic user memory")
    is_new: bool = Field(description="True if new, false if duplicate")

class MemoryDecision(BaseModel):
    should_write: bool
    memories: List[MemoryItem] = Field(default_factory=list)

# Extraction prompt prevents duplicates
MEMORY_PROMPT = """
CURRENT USER DETAILS (existing memories):
{user_details_content}

TASK:
- Extract user-specific info worth storing long-term
- For each item, set is_new=true ONLY if it adds NEW information
- If same meaning as existing, set is_new=false
"""
```

#### Merged Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MERGED LTM WORKFLOW                               │
│                                                                      │
│  User Message: "Hi, my name is Aafi and I teach AI on YouTube"       │
│                              │                                       │
│                              ▼                                       │
│  ┌───────┐         ┌──────────────────┐         ┌─────────────────┐ │
│  │ START │────────>│   remember_node  │────────>│    chat_node    │ │
│  └───────┘         └──────────────────┘         └────────┬────────┘ │
│                              │                           │          │
│                    ┌─────────┴─────────┐                 │          │
│                    ▼                   ▼                 │          │
│              Read Existing       Write New               │          │
│              Memories            Memories                │          │
│                    │                   │                 │          │
│                    └─────────┬─────────┘                 │          │
│                              │                           │          │
│                              ▼                           ▼          │
│                    ┌──────────────────────────────────────────────┐ │
│                    │              InMemoryStore                    │ │
│                    │  ("user", "u1", "details"):                   │ │
│                    │    - "Name: Aafi"                             │ │
│                    │    - "Teaches AI on YouTube"                  │ │
│                    └──────────────────────────────────────────────┘ │
│                                                                      │
│  Response: "Nice to meet you, Aafi! As someone who teaches AI..."    │
│                              │                                       │
│                              ▼                                       │
│                          ┌───────┐                                   │
│                          │  END  │                                   │
│                          └───────┘                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 📕 4.4 Parallel Evaluation Workflow (langgraph_essay.py)

#### Fan-Out Pattern for Multi-Dimensional Scoring

```python
# Three parallel evaluation nodes merge into final_evaluation
graph.add_edge(START, "evaluate_language")
graph.add_edge(START, "evaluate_analysis")     # Fan-out from START
graph.add_edge(START, "evaluate_thought")

graph.add_edge("evaluate_language", "final_evaluation")
graph.add_edge("evaluate_analysis", "final_evaluation")   # Fan-in to final
graph.add_edge("evaluate_thought", "final_evaluation")

graph.add_edge("final_evaluation", END)
```

#### Parallel Execution Diagram

```
                           ┌───────┐
                           │ START │
                           └───┬───┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
        ┌────────────┐  ┌────────────┐  ┌────────────┐
        │ evaluate   │  │ evaluate   │  │ evaluate   │
        │ _language  │  │ _analysis  │  │ _thought   │
        │            │  │            │  │            │
        │ Score: 3/10│  │ Score: 4/10│  │ Score: 5/10│
        └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  final_evaluation   │
                    │                     │
                    │  Avg Score: 4.0/10  │
                    │  Combined Feedback  │
                    └──────────┬──────────┘
                               │
                               ▼
                           ┌───────┐
                           │  END  │
                           └───────┘
```

---

### 📘 4.5 Human-in-the-Loop (hitl_example.py)

#### Interrupt Pattern for Human Approval

```python
from langgraph.types import interrupt, Command

@tool
def purchase_stock(symbol: str, quantity: int) -> str:
    """Purchase stock - requires human approval."""
    # Pause execution and return control to human
    decision = interrupt(f"Approve buying {quantity} shares of {symbol}? (yes/no)")
    
    if decision.lower() == "yes":
        return f"SUCCESS: Purchased {quantity} shares of {symbol}"
    else:
        return f"CANCELLED: Purchase declined"

# Resume execution with human decision
result = chatbot.invoke(
    Command(resume="yes"),  # Human's decision
    config={"configurable": {"thread_id": thread_id}}
)
```

#### HITL Flow Diagram

```
User: "Buy 10 shares of AAPL"
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│                        Graph Execution                        │
│                                                               │
│  chat_node ──> LLM decides to call purchase_stock tool        │
│                              │                                │
│                              ▼                                │
│              ┌────────────────────────────────┐               │
│              │      purchase_stock tool       │               │
│              │                                │               │
│              │  interrupt("Approve buying     │               │
│              │   10 shares of AAPL?")         │               │
│              │              │                 │               │
│              │              │ PAUSE           │               │
│              └──────────────┼─────────────────┘               │
│                             │                                 │
│ ════════════════════════════╪════════════════════════════════ │
│              EXECUTION PAUSED - WAITING FOR HUMAN             │
│ ════════════════════════════╪════════════════════════════════ │
└─────────────────────────────┼─────────────────────────────────┘
                              │
                              ▼
              Terminal: "HITL: Approve buying 10 shares of AAPL?"
              Human Input: "yes"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│   chatbot.invoke(Command(resume="yes"), config)              │
│                              │                               │
│                              ▼                               │
│   purchase_stock receives "yes", returns success message     │
│                              │                               │
│                              ▼                               │
│   chat_node formulates final response                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Bot: "Successfully placed order for 10 shares of AAPL"
```

---

### 📗 4.6 Full RAG Chatbot (app.py + backend.py)

#### Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           STREAMLIT UI (app.py)                          │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │
│  │    Sidebar      │  │              Chat Interface                  │   │
│  │  - New Chat     │  │  ┌─────────────────────────────────────────┐│   │
│  │  - Chat History │  │  │ User: "What does the document say..."  ││   │
│  │  - PDF Upload   │  │  │ Bot: "According to the document..."    ││   │
│  │  - PDF Info     │  │  └─────────────────────────────────────────┘│   │
│  └─────────────────┘  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (backend.py)                             │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     LangGraph State Machine                         │ │
│  │                                                                     │ │
│  │    ┌───────┐         ┌────────────┐         ┌──────────────┐       │ │
│  │    │ START │────────>│ chat_node  │────────>│ tools_node   │       │ │
│  │    └───────┘         └─────┬──────┘         └──────┬───────┘       │ │
│  │                            │                        │               │ │
│  │                            │  tools_condition       │               │ │
│  │                            │  (should call tools?)  │               │ │
│  │                            │                        │               │ │
│  │                            └────────────────────────┘               │ │
│  │                                                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                      │                                   │
│                                      ▼                                   │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                          TOOL SUITE                                 │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌───────────────┐  │ │
│  │  │ web_search  │ │ calculator  │ │ get_stock  │ │document_search│  │ │
│  │  │ (DuckDuckGo)│ │ (eval)      │ │ (Alpha V.) │ │ (ChromaDB)    │  │ │
│  │  └─────────────┘ └─────────────┘ └────────────┘ └───────┬───────┘  │ │
│  └─────────────────────────────────────────────────────────┼──────────┘ │
│                                                             │            │
│                                                             ▼            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    PDF INGESTION PIPELINE                           │ │
│  │                                                                     │ │
│  │   PDF Bytes ──> PDFPlumberLoader ──> RecursiveTextSplitter         │ │
│  │                                              │                      │ │
│  │                                              ▼                      │ │
│  │                              ┌───────────────────────────────┐      │ │
│  │                              │        ChromaDB               │      │ │
│  │                              │  Collection: doc_{hash}       │      │ │
│  │                              │  Embeddings: nomic-embed-text │      │ │
│  │                              │  (Ollama local)               │      │ │
│  │                              └───────────────────────────────┘      │ │
│  │                                                                     │ │
│  │   Features:                                                         │ │
│  │   - Content-hash based deduplication (same PDF = reuse embeddings) │ │
│  │   - Persistent storage across sessions                             │ │
│  │   - Thread-scoped retriever access                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    ASYNC CHECKPOINTING                              │ │
│  │  AsyncSqliteSaver ──> checkpoints.db                                │ │
│  │  - Per-thread conversation persistence                              │ │
│  │  - Async for non-blocking Streamlit                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Document Deduplication Flow

```
PDF Upload
    │
    ▼
┌────────────────────────────────────────────────────────────────┐
│  Compute SHA256 Hash of file_bytes                              │
│  hash = "977bbe4fd0b16b62..."                                   │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Check document_hashes.json  │
              │  Is hash already processed?  │
              └──────────────┬───────────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
    ┌───────────────┐                 ┌───────────────┐
    │   CACHE HIT   │                 │  CACHE MISS   │
    │               │                 │               │
    │ Load existing │                 │ Process PDF:  │
    │ collection:   │                 │ - Load pages  │
    │ doc_{hash}    │                 │ - Chunk text  │
    │               │                 │ - Embed chunks│
    │ ⚡ Instant    │                 │ - Store in    │
    │               │                 │   ChromaDB    │
    └───────┬───────┘                 └───────┬───────┘
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Create retriever for thread  │
              │  _THREAD_RETRIEVERS[tid] = r  │
              └──────────────────────────────┘
```

### 🔧 Technologies Used (Task-4)
- **LangGraph**: StateGraph, MemorySaver, AsyncSqliteSaver, InMemoryStore
- **Vector DB**: ChromaDB (persistent), Ollama embeddings (nomic-embed-text)
- **PDF Processing**: PDFPlumber, RecursiveCharacterTextSplitter
- **Tools**: DuckDuckGo, Calculator, Stock API, Document Search
- **Model**: `llama-3.1-8b-instant` (via Groq)
- **Async**: aiosqlite, httpx

---

## 📚 Key Concepts Reference

### LangChain vs LangGraph Comparison

| Aspect | LangChain | LangGraph |
|--------|-----------|-----------|
| **Primary Use** | Linear chains & simple agents | Complex stateful workflows |
| **State Management** | Manual (session state) | Built-in StateGraph |
| **Checkpointing** | External implementation | Native MemorySaver/SqliteSaver |
| **Branching** | Limited | Full graph control |
| **Human-in-Loop** | Manual interrupts | Native `interrupt()` |
| **Long-Term Memory** | External stores | Built-in InMemoryStore |

### Memory Types Overview

| Type | Scope | Persistence | Use Case |
|------|-------|-------------|----------|
| **Chat History** | Single conversation | Session | Context window |
| **Thread Memory** | Conversation thread | Checkpoint DB | Multi-turn conversations |
| **Long-Term Memory** | Per user | InMemoryStore | User preferences/profile |
| **RAG Memory** | Per document | Vector DB | Document knowledge |

### Tool Selection Decision Tree

```
User Query
    │
    ├── Contains "document", "PDF", "uploaded"?
    │   └── YES ──> document_search
    │
    ├── Contains math operators or "calculate"?
    │   └── YES ──> calculator
    │
    ├── Contains "stock", "price", "$"?
    │   └── YES ──> get_stock_price
    │
    └── General knowledge / current events?
        └── YES ──> web_search
```

---

## 📝 How to Add New Tasks

### Template for New Task Documentation

```markdown
## 📘 Task-N: [Task Title]

### 🎯 Learning Objectives
- Objective 1
- Objective 2

### 🏗️ Architecture
[ASCII diagram of system architecture]

### 📝 Key Code Patterns
[Code snippets with explanations]

### 📊 Data Flow / Concept Diagram
[Visual representation of flow]

### 🔧 Technologies Used
- List of technologies and their roles
```

### Steps to Add a New Task

1. **Create folder**: `task-N/`
2. **Add requirements.txt**: List dependencies
3. **Implement code**: Follow existing patterns
4. **Update this README**:
   - Add to "Repository Structure"
   - Add to "Learning Progress" table
   - Create full documentation section
   - Update "Key Concepts Reference" if new concepts

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Ollama (for local embeddings in Task-4)
- Groq API key

### Environment Setup

```bash
# Clone repository
git clone <repo-url>
cd training

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies for specific task
pip install -r task-N/requirements.txt

# Create .env file
echo "GROQ_API_KEY=your-key-here" > .env
```

### Running Applications

```bash
# Task 1, 2, 3, 4 (Streamlit apps)
streamlit run task-N/app.py

# Task 4 - HITL example (CLI)
python task-4/hitl_example.py

# Task 4 - Essay evaluator
python task-4/langgraph_essay.py
```

### Ollama Setup (for Task-4 embeddings)

```bash
# Install Ollama
# Download from https://ollama.ai

# Pull embedding model
ollama pull nomic-embed-text

# Verify running
curl http://127.0.0.1:11434/api/tags
```

---

## 📖 Resources

### Official Documentation
- [LangChain Docs](https://python.langchain.com/docs/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Groq API](https://console.groq.com/docs)
- [ChromaDB](https://docs.trychroma.com/)
- [Streamlit](https://docs.streamlit.io/)

### Recommended Learning Path
1. LangChain Expression Language (LCEL) basics
2. Prompt engineering patterns
3. Agent architectures (ReAct, Tool-Calling)
4. LangGraph state machines
5. Memory patterns (Short-term, Long-term, RAG)
6. Human-in-the-Loop systems
7. Production deployment patterns

---

<div align="center">

**Last Updated**: January 2026

Made with ❤️ for learning GenAI & Agentic AI

</div>
