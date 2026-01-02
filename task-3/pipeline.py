import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from llm import get_llm
from config import PROMPT_DIR


# -------------------------
# Helpers
# -------------------------

def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.
    """
    prompt_path = Path(PROMPT_DIR) / f"{prompt_name}.txt"
    
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}\n"
            f"Available prompt files in {PROMPT_DIR}: {list(Path(PROMPT_DIR).glob('*.txt'))}"
        )
    
    return prompt_path.read_text(encoding="utf-8")


def repair_json(json_text: str) -> str:
    """
    Attempt to repair common JSON malformation issues from LLM output.
    Specifically handles missing commas between object properties.
    """
    import re
    
    # Fix missing commas after closing brackets/braces before new string keys
    # Pattern: ] or } followed by whitespace/newline and "key" (missing comma)
    # This is the most common issue: "points": [...] "relied_facts": [...]
    json_text = re.sub(r'([\]}])\s*\n\s*(")', r'\1,\n\2', json_text)
    json_text = re.sub(r'([\]}])\s+(")', r'\1, \2', json_text)
    
    # Fix missing commas after closing brackets before opening braces
    # Pattern: ] followed by { (missing comma)
    json_text = re.sub(r'([\]}])\s*\n\s*(\{)', r'\1,\n\2', json_text)
    json_text = re.sub(r'([\]}])\s+(\{)', r'\1, \2', json_text)
    
    # Fix missing commas after string values before new keys (less common but possible)
    # Pattern: "value"\n"key" where value is not in an array
    # Be more careful here - only match if it looks like a property boundary
    json_text = re.sub(r'(")\s*\n\s*(")', r'\1,\n\2', json_text)
    
    # Remove trailing commas before closing braces/brackets (not valid JSON)
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    
    # Fix double commas that might result from repairs
    json_text = re.sub(r',\s*,', r',', json_text)
    
    # Fix triple commas (shouldn't happen but be safe)
    json_text = re.sub(r',\s*,\s*,', r',', json_text)
    
    return json_text


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text that might contain markdown code blocks or extra text.
    """
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Try to find JSON in markdown code blocks
    # Match ```json or ``` followed by content and closing ```
    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block_match:
        # Extract content and try to find balanced JSON
        content = code_block_match.group(1)
        # Find balanced braces in the content
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(content):
            if char == '{':
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    return content[start_idx:i+1]
    
    # Try to find JSON object directly (match balanced braces)
    brace_count = 0
    start_idx = -1
    for i, char in enumerate(text):
        if char == '{':
            if start_idx == -1:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                return text[start_idx:i+1]
    
    # If no balanced JSON found, return the original text
    return text


def run_llm(
    prompt_text: str, 
    variables: Dict[str, Any],
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run LLM with a prompt and return parsed JSON output.
    
    Args:
        prompt_text: The system prompt text
        variables: Variables to pass to the prompt
        max_tokens: Optional max tokens override (defaults to config value)
    """
    llm = get_llm(max_tokens=max_tokens)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_text),
            ("human", "{input}")
        ]
    )

    chain = prompt | llm | StrOutputParser()

    raw_output = chain.invoke(
        {
            "input": json.dumps(variables, ensure_ascii=False)
        }
    )

    # Check if output is empty
    if not raw_output or not raw_output.strip():
        raise ValueError(
            "LLM returned empty output. This might indicate an API error or rate limit."
        )

    # Extract JSON from the output (might be wrapped in markdown or have extra text)
    json_text = extract_json_from_text(raw_output)
    
    # Check if extracted text is still empty
    if not json_text or not json_text.strip():
        raise ValueError(
            f"Could not extract JSON from LLM output.\n"
            f"Raw output: {raw_output[:500]}"
        )
    
    # Try parsing the JSON
    original_error = None
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        original_error = e
        # If parsing fails, try to repair common JSON issues
        try:
            repaired_json = repair_json(json_text)
            return json.loads(repaired_json)
        except json.JSONDecodeError as repair_error:
            # Both original and repaired JSON failed - raise with details
            pass
    
    # If we get here, both attempts failed
    try:
        repaired_json = repair_json(json_text)
        # One final attempt with repaired JSON
        return json.loads(repaired_json)
    except json.JSONDecodeError as repair_error:
        # Final attempt failed, raise with comprehensive error message
        pass
    
    # All attempts failed - check if truncated and provide helpful error
    is_truncated = False
    if json_text.strip():
        stripped = json_text.rstrip()
        if stripped and not stripped.endswith('}'):
            open_braces = stripped.count('{')
            close_braces = stripped.count('}')
            if open_braces > close_braces:
                is_truncated = True
    
    # Build comprehensive error message
    error_msg = (
        f"LLM did not return valid JSON.\n"
        f"JSON decode error: {str(original_error)}\n"
    )
    
    if is_truncated:
        error_msg += (
            f"\n⚠️  The JSON appears to be TRUNCATED (incomplete response).\n"
            f"This usually means the response exceeded the token limit.\n"
            f"Consider increasing max_tokens or simplifying the input.\n"
        )
    else:
        error_msg += (
            f"\n⚠️  The JSON contains syntax errors (e.g., missing commas).\n"
            f"Attempted automatic repair but it failed.\n"
        )
    
    error_msg += (
        f"\nRaw output (first 1500 chars):\n{raw_output[:1500]}\n"
        f"\nExtracted JSON text (first 1500 chars):\n{json_text[:1500]}"
    )
    
    if len(raw_output) > 1500:
        error_msg += f"\n\n... (output truncated, total length: {len(raw_output)} chars)"
    
    raise ValueError(error_msg) from original_error


# -------------------------
# Pipeline stages
# -------------------------

def understand_case(case_text: str) -> Dict[str, Any]:
    """
    Stage 1: Case understanding and paraphrasing.
    """
    prompt_text = load_prompt("understand_case")

    return run_llm(
        prompt_text=prompt_text,
        variables={
            "case_text": case_text
        }
    )


def extract_facts(understanding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage 2: Extract material, procedural facts and evidence.
    """
    prompt_text = load_prompt("extract_facts")

    return run_llm(
        prompt_text=prompt_text,
        variables={
            "understanding": understanding
        }
    )


def identify_issues(
    facts: Dict[str, Any],
    follow_up: Optional[str] = None
) -> List[str]:
    """
    Stage 3: Identify legal issues.
    Follow-up questions may slightly reframe the issues.
    """
    prompt_text = load_prompt("identify_issues")

    return run_llm(
        prompt_text=prompt_text,
        variables={
            "facts": facts,
            "follow_up": follow_up or ""
        }
    )["issues"]


def generate_arguments(
    facts: Dict[str, Any],
    issues: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Stage 4: Generate arguments for both sides per issue.
    Uses higher token limit due to potentially large output.
    """
    prompt_text = load_prompt("generate_arguments")

    # Use higher token limit for argument generation (can be large with multiple issues)
    return run_llm(
        prompt_text=prompt_text,
        variables={
            "facts": facts,
            "issues": issues
        },
        max_tokens=4096  # Increased for complex argument generation
    )


def predict_judgment(
    facts: Dict[str, Any],
    issues: List[str],
    arguments: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Stage 5: Predict likely judgment with confidence and assumptions.
    Uses higher token limit due to potentially large input (all arguments).
    """
    prompt_text = load_prompt("predict_judgement")

    return run_llm(
        prompt_text=prompt_text,
        variables={
            "facts": facts,
            "issues": issues,
            "arguments": arguments
        },
        max_tokens=3072  # Increased for judgment prediction with multiple issues
    )
