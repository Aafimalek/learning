# 🔬 Task 6: Research Agent

A robust, multi-stage research agent system built with **LangGraph** and **ChatGroq (Llama 3.3 70B)**. The system reduces uncertainty step by step, survives partial failure gracefully, and synthesizes information from multiple web sources into well-cited answers.

## 🎯 Overview

This is not just a "research agent" — it's a system designed to:
- **Reduce uncertainty step by step** through structured planning
- **Survive partial failures** with graceful degradation at every stage
- **Know when it knows enough** through cross-source verification

## 🏗️ Architecture

```
User Question
     ↓
┌─────────────────────────────────────────────────────────────┐
│                    PLANNER NODE                             │
│  • Converts vague intent → concrete research plan           │
│  • Generates 3-5 specific search queries                    │
│  • Defines quality constraints for sources                  │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│                    SEARCH NODE                              │
│  • Executes multiple searches via Tavily API                │
│  • Captures metadata: URL, title, date, confidence          │
│  • Handles: timeouts, rate limits, empty results            │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│                    READER NODE                              │
│  • Fetches full article content (httpx + BeautifulSoup)     │
│  • Fallback: LangChain WebBaseLoader                        │
│  • Final fallback: snippet-only extraction                  │
│  • Extracts: claims, evidence, stats, limitations, bias     │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│                   VERIFIER NODE                             │
│  • Cross-checks claims across multiple sources              │
│  • Identifies: confirmed, disputed, single-source claims    │
│  • Calculates source agreement score                        │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│                  SYNTHESIZER NODE                           │
│  • Summarizes ACROSS sources (not per source)               │
│  • Rates evidence strength: STRONG/MODERATE/WEAK            │
│  • Identifies open questions                                │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│                    ANSWER NODE                              │
│  • Generates structured Markdown answer                     │
│  • Includes inline citations                                │
│  • Adds confidence & limitations section                    │
└─────────────────────────────────────────────────────────────┘
     ↓
Final Answer + Citations
```

## 🔑 Key Design Principles

### 1. Tools Never Throw Exceptions
Every tool returns a standardized `ToolResponse`:
```python
class ToolResponse(BaseModel):
    success: bool
    data: Optional[dict | list | str] = None
    error: Optional[str] = None
    retry_suggestion: Optional[str] = None
```

### 2. Graceful Degradation at Every Stage
```
if success → next step
if error → retry with modification → fallback → log → continue
```

- **Search fails** → Retry with simplified query → Log failure → Continue with partial results
- **Reader fails** → Try LangChain loader → Fall back to snippet-only → Never silently drop sources
- **Verification fails** → Continue with lower confidence
- **Never hard-stop** unless all fallbacks fail

### 3. Three Types of State (LangGraph)
| State Type | Contents | Purpose |
|------------|----------|---------|
| **Short-term** | `current_step`, `retry_count`, tool outputs | Current execution context |
| **Research Memory** | `research_plan`, `search_results`, `extracted_notes`, `verification`, `synthesis` | Accumulated knowledge |
| **Failure Memory** | `failures` list with operation, target, error, timestamp | Learning from failures |

### 4. Extract Before Synthesizing
Reader outputs are **structured notes**, not prose:
```python
class ExtractedNotes(BaseModel):
    url: str
    title: str
    key_claims: list[str]      # Main assertions
    evidence: list[str]        # Supporting facts/studies
    data_stats: list[str]      # Numbers, percentages, dates
    limitations: list[str]     # Caveats, gaps
    author_bias: Optional[str] # Detected perspective
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    extraction_method: Literal["FULL", "SNIPPET_ONLY", "FAILED"]
```

### 5. Verification Layer (Critical!)
Before synthesis, the system cross-checks:
- **Confirmed points**: Multiple sources agree
- **Disputed points**: Sources contradict each other
- **Single-source claims**: Flagged for caution

This reduces hallucinations more than any prompt engineering.

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **LLM** | ChatGroq (Llama 3.3 70B Versatile) |
| **Orchestration** | LangGraph (state machine workflow) |
| **Web Search** | Tavily API (LLM-optimized search) |
| **Web Scraping** | httpx + BeautifulSoup4 + lxml |
| **Fallback Scraper** | LangChain WebBaseLoader |
| **Schema Validation** | Pydantic v2 |
| **Package Management** | uv (recommended) or pip |

## 📦 Installation

### Using uv (Recommended)
```bash
cd task-6
uv venv
uv pip install -r requirements.txt
```

### Using pip
```bash
cd task-6
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## ⚙️ Configuration

1. Create a `.env` file in the task-6 directory:
```bash
# Required API Keys
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

2. Get your API keys:
   - **Groq**: https://console.groq.com/keys (free tier available)
   - **Tavily**: https://tavily.com/ (free tier: 1000 searches/month)

## 🚀 Usage

### Command Line - Single Query
```bash
python main.py "What are the latest developments in quantum computing?"
```

### Command Line - Interactive Mode
```bash
python main.py --interactive
```

### Command Line - Quiet Mode (minimal output)
```bash
python main.py -q "Compare React vs Vue.js for large applications"
```

### Programmatic Usage
```python
from graph import run_research

result = run_research(
    question="What are the best practices for microservices architecture?",
    verbose=True
)

print(result["answer"])       # Final synthesized answer
print(result["citations"])    # List of source URLs
print(result["sources_used"]) # Number of sources processed
print(result["failures"])     # Any logged failures
print(result["plan"])         # The research plan that was executed
```

## 📁 File Structure

```
task-6/
├── main.py              # CLI entry point with argument parsing
├── graph.py             # LangGraph workflow definition & routing
├── agents.py            # All agent nodes (planner, search, reader, etc.)
├── tools.py             # Tool wrappers (SearchTool, ReaderTool)
├── schemas.py           # Pydantic models & TypedDict state
├── pyproject.toml       # Project metadata & uv dependencies
├── requirements.txt     # pip-compatible dependencies
├── .env                 # Your API keys (create this)
├── uv.lock              # uv lockfile
└── README.md            # This documentation
```

## 🔍 Agent Node Details

### Planner Node (`planner_node`)
**Purpose**: Reduce entropy before searching

**Input**: Raw user question  
**Output**: Structured `ResearchPlan`
```python
{
    "objective": "What we're trying to learn",
    "sub_questions": ["Specific aspect 1", "Specific aspect 2"],
    "search_queries": ["query 1", "query 2", "query 3"],
    "quality_constraints": ["Prefer peer-reviewed", "Recent sources"],
    "max_searches": 5,
    "max_articles_per_search": 3
}
```

### Search Node (`search_node`)
**Purpose**: Breadth-first, shallow search

**Tools Used**: `SearchTool` (Tavily API)  
**Strategy**: Multiple small searches > one big query  
**Captures per result**:
- URL, title, source domain
- Publication date (when available)
- Snippet preview
- Confidence hint (HIGH/MEDIUM/LOW based on domain)

### Reader Node (`reader_node`)  
**Purpose**: Extract notes, NOT summaries

**Fetch Pipeline**:
1. Primary: `httpx` + `BeautifulSoup4` (fast, reliable)
2. Fallback: `LangChain WebBaseLoader`
3. Final: Snippet-only extraction (never drop a source)

**LLM Extraction**: Uses Groq to extract structured notes from content

### Verifier Node (`verification_node`)
**Purpose**: Cross-check before synthesis

**Output**:
```python
{
    "confirmed_points": ["Point agreed by multiple sources"],
    "disputed_points": ["Source A says X, Source B says Y"],
    "single_source_claims": ["Claim from only one source"],
    "source_agreement_score": 0.75  # 0-1 scale
}
```

### Synthesizer Node (`synthesis_node`)
**Purpose**: Compress meaning across sources

**Anti-pattern**: "Article A says..., Article B says..."  
**Correct**: "Across 7 sources, there is consensus that X. Two sources dispute Y."

**Output**:
```python
{
    "findings": [
        {
            "finding": "Main synthesized point",
            "evidence_strength": "STRONG",  # STRONG/MODERATE/WEAK
            "supporting_sources": ["url1", "url2"],
            "contradicting_sources": []
        }
    ],
    "open_questions": ["What remains unclear"],
    "confidence_summary": "Overall reliability assessment"
}
```

### Answer Node (`answer_node`)
**Purpose**: Generate human-readable response

**Output Format**:
- Structured Markdown with headers
- Bullet points for key findings
- Citations in `[Title](URL)` format
- "Confidence & Limitations" section

## 📊 Confidence Levels

### Source Confidence (assigned during search)
| Level | Domains |
|-------|---------|
| **HIGH** | `.gov`, `.edu`, `nature.com`, `science.org`, `arxiv.org`, `pubmed`, `ieee.org`, `acm.org`, `springer.com` |
| **MEDIUM** | Established news, reputable tech blogs |
| **LOW** | `reddit.com`, `quora.com`, `medium.com`, blogs, opinion pieces, forums |

### Evidence Strength (assigned during synthesis)
| Level | Criteria |
|-------|----------|
| **STRONG** | Multiple reliable sources agree |
| **MODERATE** | Some agreement or mixed confidence sources |
| **WEAK** | Single source or low-confidence sources only |

## 🛡️ Error Handling

The system is designed to **never hard-stop** unless absolutely necessary:

```
Search timeout     → Retry with simplified query → Continue with partial results
HTTP 429 (rate)    → Log failure → Continue with other queries
Parse failure      → Try LangChain → Fall back to snippet → Mark LOW confidence
LLM error          → Use fallback response → Continue pipeline
```

All failures are logged in state for debugging:
```python
{
    "operation": "read",
    "target": "https://example.com/article",
    "error": "Timeout after 20s",
    "timestamp": "2026-01-09T10:30:00",
    "retries_attempted": 2
}
```

## 📝 Example Output

```
======================================================================
📋 FINAL ANSWER
======================================================================
### Key Findings

* **React has a larger ecosystem and community**: Across 8 sources, React 
  consistently shows larger npm downloads and more third-party libraries
  [Source 1](url1), [Source 2](url2)

* **Vue.js offers gentler learning curve**: Multiple sources agree Vue's
  template syntax is more approachable for beginners [Source 3](url3)

### Confidence & Limitations

The findings are based on 13 sources with moderate overall agreement.
Some claims about performance are disputed between sources.

----------------------------------------
📚 SOURCES:
  [1] https://blog.logrocket.com/...
  [2] https://dev.to/...
  ...
======================================================================
```

## 🔧 Dependencies

```
langchain>=0.3.0
langchain-groq>=0.2.0
langchain-community>=0.3.0
langgraph>=0.2.0
tavily-python>=0.5.0
httpx>=0.27.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

## 📄 License

MIT
