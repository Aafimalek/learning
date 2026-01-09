"""
Research Agent - Main Entry Point

A system that reduces uncertainty step by step, survives partial failure,
and knows when it knows enough.

Usage:
    python main.py "Your research question here"
    python main.py --interactive
"""

import os
import sys
import argparse
from dotenv import load_dotenv
import os 
# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

def check_environment():
    """Verify required environment variables are set."""
    required_vars = {
        "GROQ_API_KEY": "Get from https://console.groq.com/keys",
        "TAVILY_API_KEY": "Get from https://tavily.com/"
    }
    
    missing = []
    for var, help_text in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  • {var}: {help_text}")
    
    if missing:
        print("❌ Missing required environment variables:\n")
        print("\n".join(missing))
        print("\nCreate a .env file with these variables or set them in your environment.")
        return False
    return True


def run_single_query(question: str, verbose: bool = True):
    """Run a single research query."""
    from graph import run_research
    
    print("\n" + "=" * 70)
    print("🔬 RESEARCH AGENT")
    print("=" * 70)
    
    result = run_research(question, verbose=verbose)
    
    print("\n" + "=" * 70)
    print("📋 FINAL ANSWER")
    print("=" * 70)
    print(result["answer"])
    
    if result["citations"]:
        print("\n" + "-" * 40)
        print("📚 SOURCES:")
        for i, url in enumerate(result["citations"], 1):
            print(f"  [{i}] {url}")
    
    if result.get("failures"):
        print("\n" + "-" * 40)
        print(f"⚠️ {len(result['failures'])} operations failed (handled gracefully)")
    
    print("\n" + "=" * 70)
    return result


def run_interactive():
    """Run in interactive mode."""
    print("\n" + "=" * 70)
    print("🔬 RESEARCH AGENT - Interactive Mode")
    print("=" * 70)
    print("Type your research questions. Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            question = input("\n🔍 Question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            run_single_query(question, verbose=True)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Research Agent - Intelligent web research with verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "What are the latest developments in quantum computing?"
  python main.py "Compare React vs Vue.js for large applications"
  python main.py --interactive
  python main.py -q "Climate change impacts on agriculture" --quiet

Environment Variables:
  GROQ_API_KEY     - API key for Groq LLM (required)
  TAVILY_API_KEY   - API key for Tavily search (required)
        """
    )
    
    parser.add_argument(
        "question",
        nargs="?",
        help="Research question to answer"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Determine mode
    if args.interactive:
        run_interactive()
    elif args.question:
        run_single_query(args.question, verbose=not args.quiet)
    else:
        parser.print_help()
        print("\n💡 Tip: Use --interactive for multiple queries")


if __name__ == "__main__":
    main()
