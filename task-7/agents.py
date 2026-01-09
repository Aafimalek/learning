"""
Specialized Agents.

Each agent is DUMB ON PURPOSE:
- Assumes intent is already correct
- Has ZERO responsibility for routing
- Is optimized for ONE job only

This separation prevents prompt leakage and tool misuse.
"""

import os
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from schemas import (
    GraphState,
    IntentType,
    AgentResponse,
    BlogOutput,
    CodeOutput,
    QNAOutput,
    ResearchOutput,
    ClarificationOutput,
    LogEntry
)

load_dotenv()


# ============================================================================
# LLM Factory
# ============================================================================

def get_llm(temperature: float = 0.7, model: str = "llama-3.1-8b-instant"):
    """Create a Groq LLM instance."""
    return ChatGroq(
        model=model,
        temperature=temperature,
        api_key=os.getenv("GROQ_API_KEY")
    )


# ============================================================================
# BLOG AGENT
# ============================================================================

BLOG_SYSTEM_PROMPT = """You are a professional blog writer.

Your job is to write engaging, well-structured blog posts.

## Writing Guidelines:
- Use clear, conversational tone
- Include introduction, body with subheadings, and conclusion
- Use markdown formatting
- Aim for 500-800 words
- Make it informative yet engaging

## Structure:
1. Catchy title
2. Introduction (hook the reader)
3. Main content with 2-4 sections
4. Conclusion with takeaways

Do NOT include code unless specifically about programming.
Do NOT add references or citations (this is creative writing).
"""

def blog_agent_node(state: GraphState) -> dict:
    """Blog writing agent - optimized for long-form creative content."""
    query = state["user_query"]
    start_time = datetime.now()
    
    try:
        llm = get_llm(temperature=0.8)  # Higher creativity
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", BLOG_SYSTEM_PROMPT),
            ("human", "Write a blog post about: {query}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"query": query})
        content = result.content
        
        # Parse output
        lines = content.strip().split('\n')
        title = lines[0].replace('#', '').strip() if lines else "Untitled"
        
        output = BlogOutput(
            title=title,
            content=content,
            word_count=len(content.split()),
            tags=[]  # Could extract from content
        )
        
        response = AgentResponse(
            success=True,
            agent_type=IntentType.BLOG_WRITE,
            output=output,
            raw_output=content,
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        
        log_entry = LogEntry(
            step="blog_agent",
            query=query,
            output_length=len(content),
            metadata={"word_count": output.word_count}
        ).model_dump()
        
        return {
            "agent_response": response,
            "logs": [log_entry],
            "should_continue": False
        }
        
    except Exception as e:
        return _handle_agent_error(state, "blog_agent", e)


# ============================================================================
# CODE AGENT
# ============================================================================

CODE_SYSTEM_PROMPT = """You are a code generation specialist.

Your job is to write clean, working code.

## Guidelines:
- Write production-quality code
- Include necessary imports
- Use proper naming conventions
- Add brief inline comments for complex logic
- DO NOT explain unless asked - just provide the code

## Output Format:
```language
// code here
```

If multiple files are needed, separate them clearly with filename comments.
"""

def code_agent_node(state: GraphState) -> dict:
    """Code generation agent - optimized for code output."""
    query = state["user_query"]
    start_time = datetime.now()
    
    try:
        llm = get_llm(temperature=0.2)  # Lower temperature for determinism
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", CODE_SYSTEM_PROMPT),
            ("human", "{query}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"query": query})
        content = result.content
        
        # Try to extract language from code block
        language = "python"  # default
        if "```" in content:
            first_block = content.split("```")[1] if "```" in content else ""
            first_line = first_block.split('\n')[0].strip().lower()
            if first_line and not first_line.startswith('//'):
                language = first_line
        
        # Extract code from markdown blocks
        code = content
        if "```" in content:
            parts = content.split("```")
            if len(parts) >= 2:
                code_block = parts[1]
                # Remove language identifier from first line
                code_lines = code_block.split('\n')
                if code_lines and not code_lines[0].strip().startswith(('import', 'from', 'def', 'class', '//', '#', 'const', 'let', 'var', 'function')):
                    code = '\n'.join(code_lines[1:])
                else:
                    code = code_block
        
        output = CodeOutput(
            language=language,
            code=code.strip(),
            explanation=None,
            dependencies=[]
        )
        
        response = AgentResponse(
            success=True,
            agent_type=IntentType.CODE,
            output=output,
            raw_output=content,
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        
        log_entry = LogEntry(
            step="code_agent",
            query=query,
            output_length=len(code),
            metadata={"language": language}
        ).model_dump()
        
        return {
            "agent_response": response,
            "logs": [log_entry],
            "should_continue": False
        }
        
    except Exception as e:
        return _handle_agent_error(state, "code_agent", e)


# ============================================================================
# QNA AGENT
# ============================================================================

QNA_SYSTEM_PROMPT = """You are a concise Q&A assistant.

Your job is to provide SHORT, FACTUAL answers.

## Guidelines:
- Keep answers to 1-3 sentences
- Be direct and factual
- No fluff or unnecessary context
- If you're not sure, say so briefly

Do NOT write essays or long explanations.
Do NOT include code unless the question is specifically about code syntax.
"""

def qna_agent_node(state: GraphState) -> dict:
    """QNA agent - optimized for short factual answers."""
    query = state["user_query"]
    start_time = datetime.now()
    
    try:
        llm = get_llm(temperature=0.3)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", QNA_SYSTEM_PROMPT),
            ("human", "{query}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"query": query})
        content = result.content.strip()
        
        output = QNAOutput(
            answer=content,
            confidence=0.8  # Could be estimated from response
        )
        
        response = AgentResponse(
            success=True,
            agent_type=IntentType.QNA,
            output=output,
            raw_output=content,
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        
        log_entry = LogEntry(
            step="qna_agent",
            query=query,
            output_length=len(content)
        ).model_dump()
        
        return {
            "agent_response": response,
            "logs": [log_entry],
            "should_continue": False
        }
        
    except Exception as e:
        return _handle_agent_error(state, "qna_agent", e)


# ============================================================================
# RESEARCH AGENT
# ============================================================================

RESEARCH_SYSTEM_PROMPT = """You are a research analyst.

Your job is to provide in-depth analysis on topics.

## Guidelines:
- Provide structured, comprehensive analysis
- Include multiple perspectives
- Use clear sections and bullet points
- Cite general knowledge (no web search)
- Be objective and balanced

## Structure:
1. Overview
2. Key Points (3-5)
3. Analysis/Comparison (if applicable)
4. Considerations/Limitations
5. Summary

Aim for depth without unnecessary length.
"""

def research_agent_node(state: GraphState) -> dict:
    """Research agent - optimized for in-depth analysis."""
    query = state["user_query"]
    start_time = datetime.now()
    
    try:
        llm = get_llm(temperature=0.5)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", RESEARCH_SYSTEM_PROMPT),
            ("human", "Provide an in-depth analysis on: {query}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"query": query})
        content = result.content
        
        # Extract key points (simple heuristic)
        key_points = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('-', '•', '*')) and len(line) > 10:
                key_points.append(line.lstrip('-•* '))
                if len(key_points) >= 5:
                    break
        
        output = ResearchOutput(
            summary=content,
            key_points=key_points,
            sources_consulted=0
        )
        
        response = AgentResponse(
            success=True,
            agent_type=IntentType.RESEARCH,
            output=output,
            raw_output=content,
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        
        log_entry = LogEntry(
            step="research_agent",
            query=query,
            output_length=len(content),
            metadata={"key_points_count": len(key_points)}
        ).model_dump()
        
        return {
            "agent_response": response,
            "logs": [log_entry],
            "should_continue": False
        }
        
    except Exception as e:
        return _handle_agent_error(state, "research_agent", e)


# ============================================================================
# CLARIFICATION AGENT
# ============================================================================

CLARIFY_SYSTEM_PROMPT = """You are a clarification assistant.

The user's query is ambiguous. Your job is to ask a clarifying question.

## Guidelines:
- Ask ONE clear question
- Provide 2-4 specific options
- Be concise and helpful
- Frame options based on what the user might want

Example:
"I'd be happy to help! Could you clarify what you're looking for?
1. A blog post about the topic
2. A quick factual answer
3. An in-depth analysis
4. Code implementation"
"""

def clarify_agent_node(state: GraphState) -> dict:
    """Clarification agent - handles ambiguous queries."""
    query = state["user_query"]
    start_time = datetime.now()
    
    try:
        llm = get_llm(temperature=0.5)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", CLARIFY_SYSTEM_PROMPT),
            ("human", "The user asked: \"{query}\"\n\nThis query is ambiguous. Ask a clarifying question with specific options.")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"query": query})
        content = result.content.strip()
        
        # Extract options (simple heuristic)
        options = []
        for line in content.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith(('-', '•'))):
                options.append(line.lstrip('0123456789.-•) '))
        
        output = ClarificationOutput(
            clarifying_question=content,
            options=options[:4],
            original_query=query
        )
        
        response = AgentResponse(
            success=True,
            agent_type=IntentType.CLARIFY,
            output=output,
            raw_output=content,
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        
        log_entry = LogEntry(
            step="clarify_agent",
            query=query,
            output_length=len(content),
            metadata={"options_count": len(options)}
        ).model_dump()
        
        return {
            "agent_response": response,
            "logs": [log_entry],
            "should_continue": False
        }
        
    except Exception as e:
        return _handle_agent_error(state, "clarify_agent", e)


# ============================================================================
# ERROR HANDLING (Shared)
# ============================================================================

def _handle_agent_error(state: GraphState, agent_name: str, error: Exception) -> dict:
    """Handle agent errors gracefully."""
    query = state.get("user_query", "")
    retry_count = state.get("retry_count", 0)
    
    log_entry = LogEntry(
        step=agent_name,
        query=query,
        error=str(error),
        metadata={"retry_count": retry_count}
    ).model_dump()
    
    response = AgentResponse(
        success=False,
        agent_type=IntentType.CLARIFY,
        error=str(error)
    )
    
    return {
        "agent_response": response,
        "error_state": str(error),
        "retry_count": retry_count + 1,
        "logs": [log_entry]
    }


# ============================================================================
# ERROR RECOVERY NODE
# ============================================================================

def error_recovery_node(state: GraphState) -> dict:
    """
    Recovery node for handling failures.
    
    Strategies:
    1. Retry with constrained prompt
    2. Downgrade output quality
    3. Provide meaningful error message
    """
    error = state.get("error_state", "Unknown error")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    query = state.get("user_query", "")
    
    log_entry = LogEntry(
        step="error_recovery",
        query=query,
        error=error,
        metadata={
            "retry_count": retry_count,
            "max_retries": max_retries
        }
    ).model_dump()
    
    if retry_count >= max_retries:
        # Give up gracefully
        response = AgentResponse(
            success=False,
            agent_type=IntentType.CLARIFY,
            raw_output=f"I apologize, but I encountered an issue processing your request: {error}\n\nPlease try rephrasing your question or breaking it into smaller parts.",
            error=error
        )
        
        return {
            "agent_response": response,
            "logs": [log_entry],
            "should_continue": False
        }
    
    # Try again with clarification
    return {
        "routed_to": "clarify_agent",
        "logs": [log_entry],
        "error_state": None
    }
