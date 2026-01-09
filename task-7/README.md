# Multi-Agent Routing System

A LangGraph-based multi-agent system with intent classification and deterministic routing.

## Architecture

```
User Query
   ↓
Intent Classifier (LLM, cheap, fast, deterministic)
   ↓
Routing Policy (rules + confidence)
   ↓
Specialized Agents (blog, code, QNA, research, clarify)
   ↓
Output
```

## Key Design Principles

### 1. Non-Overlapping Intents

| Intent | Description | Output Shape | Example |
|--------|-------------|--------------|---------|
| BLOG_WRITE | Long-form creative writing | Markdown article | "Write a blog on transformers" |
| CODE | Deterministic code generation | Code block | "Write a Flask API" |
| QNA | Short factual answer | Text | "What is cosine similarity?" |
| RESEARCH | In-depth analysis | Structured text | "Compare BERT vs GPT" |
| CLARIFY | Ambiguous query | Clarifying question | (internal routing) |

### 2. Pure Classifier (Not an Agent)

The classifier:
- Has NO tools
- Uses low temperature (deterministic)
- Returns structured output only
- Uses fast model (Groq llama-3.1-8b-instant)

### 3. Deterministic Routing Policy

```python
if confidence < 0.6:
    route → CLARIFY_AGENT
elif intent == BLOG_WRITE:
    route → BLOG_AGENT
...
```

LLMs are probabilistic. The routing policy adds reliability through explicit guardrails.

### 4. Dumb Specialized Agents

Each agent:
- Assumes intent is already correct
- Has zero responsibility for routing
- Is optimized for one job only

This prevents prompt leakage and tool misuse.

### 5. First-Class Error Handling

- Low confidence → Clarification agent
- Agent failure → Retry with constrained prompt
- Max retries exceeded → Graceful degradation

### 6. Logging & Introspection

Every hop is logged:
- User query
- Classified intent
- Confidence
- Chosen route
- Agent output length

## Installation

```bash
cd task-7
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
LANGSMITH_API_KEY=your_langsmith_key  # Optional
LANGSMITH_PROJECT=routing-agent
LANGSMITH_TRACING=true
```

## Usage

### Interactive Mode

```bash
python main.py
```

Commands:
- `quit` - Exit
- `logs` - Show recent logs
- `analytics` - Show 7-day analytics
- `debug` - Toggle debug mode

### Single Query

```bash
python main.py "Write a blog about machine learning"
```

### Analytics

```bash
python main.py --analytics 7  # Last 7 days
```

## Project Structure

```
task-7/
├── main.py          # Entry point
├── schemas.py       # State and output schemas
├── classifier.py    # Intent classifier node
├── router.py        # Routing policy node
├── agents.py        # Specialized agent nodes
├── graph.py         # LangGraph workflow
├── logger.py        # Logging and analytics
├── requirements.txt
├── .env
└── logs/            # Auto-created log directory
```

## Testing Individual Components

```bash
# Test classifier
python classifier.py

# Test router
python router.py

# Test graph
python graph.py
```

## Common Mistakes Avoided

❌ Letting the main agent decide routing internally → opaque, untestable
✅ Separate classifier + deterministic router

❌ Using one giant "do everything" agent → prompt spaghetti
✅ Specialized single-purpose agents

❌ No confidence threshold → silent misroutes
✅ Confidence-based routing to clarification

❌ Adding tools to the classifier → slow and noisy
✅ Pure classifier with no tools

## Extending the System

### Adding a New Intent

1. Add to `IntentType` enum in `schemas.py`
2. Add output schema in `schemas.py`
3. Create agent function in `agents.py`
4. Add route mapping in `router.py`
5. Add node and edges in `graph.py`
6. Update classifier prompt in `classifier.py`

### Tuning Confidence Threshold

Edit `RoutingConfig` in `schemas.py`:

```python
class RoutingConfig(BaseModel):
    confidence_threshold: float = 0.6  # Adjust this
```

Lower = more queries go to specialized agents (riskier)
Higher = more queries go to clarification (safer)
