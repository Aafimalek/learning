#!/usr/bin/env python
"""
Startup Idea Validator - Main Entry Point

This script runs the multi-agent startup validation crew to analyze
and validate startup ideas through comprehensive market research.
"""

import sys
import time
import warnings
from datetime import datetime

from task_13.crew import StartupValidatorCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 90  # Increased to 90 seconds for Groq rate limits
MAX_RETRY_DELAY = 300  # 5 minutes max
TASK_COMPLETION_DELAY = 30  # Delay between tasks to avoid rate limits


def run():
    """
    Run the Startup Idea Validator crew.
    
    Usage:
        task_13  # Will prompt for startup idea
        python -m task_13.main  # Alternative way to run
    """
    # Get startup idea from command line or prompt
    if len(sys.argv) > 1:
        startup_idea = " ".join(sys.argv[1:])
    else:
        startup_idea = input("Enter your startup idea to validate: ").strip()
        if not startup_idea:
            startup_idea = "AI-powered personal finance assistant for millennials"
            print(f"Using default idea: {startup_idea}")

    inputs = {
        'startup_idea': startup_idea,
        'current_year': str(datetime.now().year)
    }

    print("\n" + "=" * 60)
    print("🚀 STARTUP IDEA VALIDATOR")
    print("=" * 60)
    print(f"📝 Analyzing: {startup_idea}")
    print(f"📅 Year: {inputs['current_year']}")
    print("=" * 60 + "\n")

    # Retry loop for handling rate limits and token limits
    retries = 0
    last_error = None
    
    while retries <= MAX_RETRIES:
        try:
            result = StartupValidatorCrew().crew().kickoff(inputs=inputs)
            print("\n" + "=" * 60)
            print("✅ VALIDATION COMPLETE!")
            print("=" * 60)
            print("📁 Reports saved to the 'reports/' folder:")
            print("   - 01_market_research_report.md")
            print("   - 02_competitive_analysis_report.md")
            print("   - 03_customer_insights_report.md")
            print("   - 04_product_strategy_report.md")
            print("   - 05_final_validation_report.md")
            print("=" * 60 + "\n")
            return result
        except Exception as e:
            error_str = str(e).lower()
            last_error = e
            
            # Check if it's a rate limit or token limit error
            is_rate_limit = any(keyword in error_str for keyword in [
                'rate_limit', 'rate limit', '429', 'too many requests',
                'token', 'quota', 'exceeded', 'limit', 'capacity',
                'overloaded', 'retry'
            ])
            
            if is_rate_limit and retries < MAX_RETRIES:
                retries += 1
                # Exponential backoff with jitter
                delay = min(INITIAL_RETRY_DELAY * (2 ** (retries - 1)), MAX_RETRY_DELAY)
                
                print("\n" + "=" * 60)
                print(f"⚠️  RATE/TOKEN LIMIT HIT - Retry {retries}/{MAX_RETRIES}")
                print(f"⏳ Waiting {delay} seconds before retrying...")
                print("=" * 60 + "\n")
                
                time.sleep(delay)
                print(f"🔄 Retrying now...")
            else:
                # Not a rate limit error or max retries reached
                break
    
    raise Exception(f"An error occurred while running the crew after {retries} retries: {last_error}")


def train():
    """
    Train the crew for a given number of iterations.
    
    Usage:
        train <n_iterations> <output_filename>
    """
    if len(sys.argv) < 3:
        startup_idea = "AI-powered personal finance assistant for millennials"
    else:
        startup_idea = "AI-powered personal finance assistant for millennials"
    
    inputs = {
        "startup_idea": startup_idea,
        'current_year': str(datetime.now().year)
    }
    
    try:
        StartupValidatorCrew().crew().train(
            n_iterations=int(sys.argv[1]), 
            filename=sys.argv[2], 
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    
    Usage:
        replay <task_id>
    """
    try:
        StartupValidatorCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and return results.
    
    Usage:
        test <n_iterations> <eval_llm>
    """
    inputs = {
        "startup_idea": "AI-powered personal finance assistant for millennials",
        "current_year": str(datetime.now().year)
    }

    try:
        StartupValidatorCrew().crew().test(
            n_iterations=int(sys.argv[1]), 
            eval_llm=sys.argv[2], 
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


def run_with_trigger():
    """
    Run the crew with trigger payload (for automated/API use).
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    # Extract startup idea from trigger payload or use default
    startup_idea = trigger_payload.get(
        'startup_idea', 
        'AI-powered personal finance assistant for millennials'
    )

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "startup_idea": startup_idea,
        "current_year": str(datetime.now().year)
    }

    try:
        result = StartupValidatorCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")


if __name__ == "__main__":
    run()
