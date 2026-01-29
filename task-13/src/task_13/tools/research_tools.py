"""
Research tools for the Startup Idea Validator.
Includes web search, website scraping, and selenium-based scraping tools.
"""

from crewai_tools import SerperDevTool, ScrapeWebsiteTool, SeleniumScrapingTool

# Web Search Tool - Uses Serper.dev API for Google search results
# Requires SERPER_API_KEY environment variable
search_tool = SerperDevTool(
    n_results=10,  # Number of search results to return
)

# News Search Tool - For finding recent news articles
news_search_tool = SerperDevTool(
    n_results=10,
    search_type="news",  # Search news articles specifically
)

# Web Scraping Tool - HTTP-based scraping for static websites
# Good for extracting text content from web pages
scrape_tool = ScrapeWebsiteTool()

# Selenium Scraping Tool - Browser-based scraping for dynamic websites
# Handles JavaScript-rendered content
selenium_tool = SeleniumScrapingTool(
    wait_time=5,  # Wait time before scraping (for JS to load)
)


def get_search_tools():
    """Returns list of search-related tools."""
    return [search_tool, news_search_tool]


def get_scraping_tools():
    """Returns list of scraping tools."""
    return [scrape_tool, selenium_tool]


def get_all_tools():
    """Returns all available research tools."""
    return [search_tool, news_search_tool, scrape_tool, selenium_tool]
