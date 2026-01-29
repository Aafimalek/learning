"""
Startup Idea Validator Crew

A multi-agent system for comprehensive startup idea validation through
market research, competitive analysis, customer insights, and strategic assessment.
"""

import os
import time
import litellm
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Import research tools
from task_13.tools.research_tools import (
    search_tool,
    news_search_tool,
    scrape_tool,
    selenium_tool,
)

# =============================================================================
# LITELLM RETRY CONFIGURATION
# =============================================================================
# Configure litellm to automatically retry on rate limit errors
litellm.num_retries = 5  # Increased retries for rate limit errors
litellm.request_timeout = 180  # Increased timeout in seconds
litellm.retry_after = 30  # Wait 30 seconds between retries

# Set up retry delays (in seconds) - exponential backoff
os.environ["LITELLM_RETRY_AFTER"] = "30"
os.environ["LITELLM_MAX_RETRIES"] = "5"

# =============================================================================
# RATE LIMITING NOTE
# =============================================================================
# Groq free tier: 30 RPM, 6000 TPM for llama-3.3-70b-versatile
# We use max_rpm on agents to throttle requests


@CrewBase
class StartupValidatorCrew:
    """
    Startup Idea Validator Crew
    
    This crew consists of 5 specialized agents that work together to validate
    startup ideas through comprehensive research and analysis:
    
    1. Market Research Specialist - Analyzes market size, trends, and opportunities
    2. Competitive Intelligence Analyst - Maps the competitive landscape
    3. Customer Insights Researcher - Understands target customers and their needs
    4. Product Strategy Advisor - Evaluates product-market fit and go-to-market
    5. Business Analyst - Synthesizes all findings into a final validation report
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    # Configuration files
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # =========================================================================
    # AGENTS
    # =========================================================================

    @agent
    def market_research_specialist(self) -> Agent:
        """
        Market Research Specialist Agent
        
        Tools: Web search, news search, web scraping
        Focus: Market size, trends, growth projections, opportunities
        """
        return Agent(
            config=self.agents_config['market_research_specialist'],  # type: ignore[index]
            tools=[search_tool, news_search_tool, scrape_tool],
            max_rpm=1,  # Max 1 request per minute to stay well within rate limits
            verbose=True,
        )

    @agent
    def competitive_intelligence_analyst(self) -> Agent:
        """
        Competitive Intelligence Analyst Agent
        
        Tools: Web search, news search, web scraping, selenium scraping
        Focus: Competitor identification, SWOT analysis, market positioning
        """
        return Agent(
            config=self.agents_config['competitive_intelligence_analyst'],  # type: ignore[index]
            tools=[search_tool, news_search_tool, scrape_tool, selenium_tool],
            max_rpm=1,  # Max 1 request per minute to stay well within rate limits
            verbose=True,
        )

    @agent
    def customer_insights_researcher(self) -> Agent:
        """
        Customer Insights Researcher Agent
        
        Tools: Web search, web scraping
        Focus: Customer personas, pain points, buying behavior, willingness to pay
        """
        return Agent(
            config=self.agents_config['customer_insights_researcher'],  # type: ignore[index]
            tools=[search_tool, scrape_tool],
            max_rpm=1,  # Max 1 request per minute to stay well within rate limits
            verbose=True,
        )

    @agent
    def product_strategy_advisor(self) -> Agent:
        """
        Product Strategy Advisor Agent
        
        Tools: Web search, web scraping
        Focus: Value proposition, features, pricing, go-to-market strategy
        """
        return Agent(
            config=self.agents_config['product_strategy_advisor'],  # type: ignore[index]
            tools=[search_tool, scrape_tool],
            max_rpm=1,  # Max 1 request per minute to stay well within rate limits
            verbose=True,
        )

    @agent
    def business_analyst(self) -> Agent:
        """
        Business Analyst Agent (Final Report Synthesizer)
        
        Tools: None (synthesizes from previous reports)
        Focus: Final validation, GO/NO-GO recommendation, strategic recommendations
        """
        return Agent(
            config=self.agents_config['business_analyst'],  # type: ignore[index]
            max_rpm=1,  # Max 1 request per minute to stay well within rate limits
            verbose=True,
        )

    # =========================================================================
    # TASKS
    # =========================================================================

    @task
    def market_research_task(self) -> Task:
        """
        Market Research Task
        
        Output: reports/01_market_research_report.md
        """
        return Task(
            config=self.tasks_config['market_research_task'],  # type: ignore[index]
            output_file='reports/01_market_research_report.md',
        )

    @task
    def competitive_analysis_task(self) -> Task:
        """
        Competitive Analysis Task
        
        Output: reports/02_competitive_analysis_report.md
        """
        return Task(
            config=self.tasks_config['competitive_analysis_task'],  # type: ignore[index]
            output_file='reports/02_competitive_analysis_report.md',
        )

    @task
    def customer_research_task(self) -> Task:
        """
        Customer Research Task
        
        Output: reports/03_customer_insights_report.md
        """
        return Task(
            config=self.tasks_config['customer_research_task'],  # type: ignore[index]
            output_file='reports/03_customer_insights_report.md',
        )

    @task
    def product_strategy_task(self) -> Task:
        """
        Product Strategy Task
        
        Output: reports/04_product_strategy_report.md
        """
        return Task(
            config=self.tasks_config['product_strategy_task'],  # type: ignore[index]
            output_file='reports/04_product_strategy_report.md',
        )

    @task
    def final_validation_report_task(self) -> Task:
        """
        Final Validation Report Task
        
        This task receives context from ALL previous tasks to synthesize
        a comprehensive validation report with GO/NO-GO recommendation.
        
        Output: reports/05_final_validation_report.md
        """
        return Task(
            config=self.tasks_config['final_validation_report_task'],  # type: ignore[index]
            output_file='reports/05_final_validation_report.md',
            context=[
                self.market_research_task(),
                self.competitive_analysis_task(),
                self.customer_research_task(),
                self.product_strategy_task(),
            ],
        )

    # =========================================================================
    # CREW
    # =========================================================================

    def _step_callback(self, step_output) -> None:
        """
        Callback executed after each agent step.
        Adds a delay to avoid rate limiting.
        """
        print(f"\n⏳ Waiting 15 seconds to avoid rate limits...")
        time.sleep(15)

    def _task_callback(self, task_output) -> None:
        """
        Callback executed after each task completes.
        Adds a longer delay between tasks to reset rate limits.
        """
        print(f"\n✅ Task completed! Waiting 30 seconds before next task...")
        time.sleep(30)

    @crew
    def crew(self) -> Crew:
        """
        Creates the Startup Validator Crew
        
        Process: Sequential (each task builds on previous findings)
        Memory: Disabled (context passed explicitly through task dependencies)
        Callbacks: Added to handle rate limiting via delays
        """
        return Crew(
            agents=self.agents,  # Automatically created by @agent decorators
            tasks=self.tasks,    # Automatically created by @task decorators
            process=Process.sequential,
            verbose=True,
            step_callback=self._step_callback,  # Add delay after each agent step
            task_callback=self._task_callback,  # Add delay after each task
        )
