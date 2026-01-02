from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_experimental.utilities import PythonREPL
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field 

# Setup utilities
# PythonREPL executes code locally; use only in a safe, sandboxed environment
python_repl = PythonREPL()
wiki_wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1000)

# Define input schema for python interpreter
class PythonInterpreterInput(BaseModel):
    """Input schema for python interpreter tool."""
    code: str = Field(description="The Python code to execute. Can be an expression, statement, or multiple lines of code.")

# Wrapper function to ensure python interpreter returns clear results
def python_interpreter_wrapper(code: str) -> str:
    """Execute python code and return formatted result.
    
    Args:
        code: The Python code to execute
    """
    try:
        result = python_repl.run(code)
        # Ensure we always return something meaningful
        if not result or result.strip() == "":
            return "Code executed successfully. If this was a calculation, try using 'print(<expression>)' to see the result."
        return f"Result: {result}"
    except Exception as e:
        return f"Error executing code: {str(e)}"

tools = [
    Tool(
        name="duckduckgo_search",
        func=DuckDuckGoSearchRun().run,
        description="Search the live web for current events, news, and real-time data."
    ),
    Tool(
        name="wikipedia",
        func=WikipediaQueryRun(api_wrapper=wiki_wrapper).run,
        description="Search Wikipedia for deep historical facts and general knowledge."
    ),
    StructuredTool(
        name="python_interpreter",
        func=python_interpreter_wrapper,
        description="Execute python code for complex math or logic. Input should be a valid python expression or statement. For calculations, you can use: 'print(<expression>)' or just '<expression>'. The tool will return the result. After getting the result, provide it as your final answer to the user.",
        args_schema=PythonInterpreterInput
    )
]