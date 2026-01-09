"""
Tool wrappers for the research agent.
All tools return ToolResponse - NEVER throw exceptions up the stack.
"""

import os

# Set USER_AGENT before importing LangChain to suppress warning
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "ResearchAgent/1.0 (Python; LangChain)"

import httpx
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

from schemas import ToolResponse, SearchResult, SearchResults, ExtractedNotes


# ============================================================================
# Web Search Tool (Tavily)
# ============================================================================

class SearchTool:
    """
    Web search using Tavily API.
    This is tool-only, no LLM reasoning inside.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com"
        self.timeout = 30.0
        self.max_retries = 2
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> ToolResponse:
        """
        Execute a web search. Returns ToolResponse, never throws.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: "basic" or "advanced"
            include_domains: Optional list of domains to include
            exclude_domains: Optional list of domains to exclude
        """
        if not self.api_key:
            return ToolResponse(
                success=False,
                error="TAVILY_API_KEY not configured",
                retry_suggestion="Set TAVILY_API_KEY environment variable"
            )
        
        for attempt in range(self.max_retries + 1):
            try:
                payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": False,
                }
                
                if include_domains:
                    payload["include_domains"] = include_domains
                if exclude_domains:
                    payload["exclude_domains"] = exclude_domains
                
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/search",
                        json=payload
                    )
                
                if response.status_code == 429:
                    return ToolResponse(
                        success=False,
                        error="Rate limit exceeded",
                        retry_suggestion="Wait and retry with fewer queries"
                    )
                
                if response.status_code != 200:
                    if attempt < self.max_retries:
                        continue
                    return ToolResponse(
                        success=False,
                        error=f"API error: {response.status_code}",
                        retry_suggestion="Simplify query or try different search terms"
                    )
                
                data = response.json()
                results = []
                
                for item in data.get("results", []):
                    # Determine confidence based on source
                    confidence = self._assess_confidence(item)
                    
                    results.append(SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        source=self._extract_domain(item.get("url", "")),
                        publication_date=item.get("published_date"),
                        snippet=item.get("content", "")[:500],
                        confidence_hint=confidence
                    ))
                
                search_results = SearchResults(
                    query=query,
                    results=results
                )
                
                if not results:
                    return ToolResponse(
                        success=False,
                        error="No results found",
                        retry_suggestion="Try broader or different search terms",
                        data=search_results.model_dump()
                    )
                
                return ToolResponse(
                    success=True,
                    data=search_results.model_dump()
                )
                
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    continue
                return ToolResponse(
                    success=False,
                    error="Search timeout",
                    retry_suggestion="Simplify query"
                )
            except Exception as e:
                if attempt < self.max_retries:
                    continue
                return ToolResponse(
                    success=False,
                    error=f"Search failed: {str(e)}",
                    retry_suggestion="Try a different query"
                )
        
        return ToolResponse(
            success=False,
            error="Max retries exceeded",
            retry_suggestion="Try a completely different approach"
        )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""
    
    def _assess_confidence(self, item: dict) -> str:
        """Assess confidence based on source characteristics."""
        url = item.get("url", "").lower()
        
        # High confidence sources
        high_confidence = [
            ".gov", ".edu", "nature.com", "science.org", "arxiv.org",
            "pubmed", "ieee.org", "acm.org", "springer.com"
        ]
        
        # Low confidence sources
        low_confidence = [
            "reddit.com", "quora.com", "medium.com", "blog",
            "opinion", "forum"
        ]
        
        for domain in high_confidence:
            if domain in url:
                return "HIGH"
        
        for domain in low_confidence:
            if domain in url:
                return "LOW"
        
        return "MEDIUM"


# ============================================================================
# Web Reader Tool (Article Fetcher & Parser)
# ============================================================================

class ReaderTool:
    """
    Fetches and parses web articles.
    Uses LangChain document loaders as fallback.
    """
    
    def __init__(self):
        self.timeout = 20.0
        self.max_retries = 2
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    def fetch_article(self, url: str, snippet_fallback: Optional[str] = None) -> ToolResponse:
        """
        Fetch and parse article content. Returns ToolResponse, never throws.
        
        Args:
            url: URL to fetch
            snippet_fallback: Snippet to use if full extraction fails
        """
        # Try primary fetch with httpx + BeautifulSoup
        try:
            result = self._fetch_with_httpx(url)
            if result.success:
                return result
        except Exception as e:
            pass  # Continue to fallback
        
        # Try LangChain WebBaseLoader as fallback
        try:
            result = self._fetch_with_langchain(url)
            if result.success:
                return result
        except Exception as e:
            pass  # Continue to snippet fallback
        
        # Final fallback: use snippet if available
        if snippet_fallback:
            return ToolResponse(
                success=True,
                data={
                    "url": url,
                    "content": snippet_fallback,
                    "title": "",
                    "extraction_method": "SNIPPET_ONLY"
                }
            )
        
        return ToolResponse(
            success=False,
            error=f"Failed to fetch article: {url}",
            retry_suggestion="Try a different source"
        )
    
    def _fetch_with_httpx(self, url: str) -> ToolResponse:
        """Primary fetch method using httpx + BeautifulSoup."""
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return ToolResponse(
                    success=False,
                    error=f"HTTP {response.status_code}"
                )
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "ad", "advertisement"]):
                tag.decompose()
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string or ""
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)
            
            # Extract main content (try common article containers)
            content = ""
            
            # Try specific article containers
            article_selectors = [
                "article",
                '[role="main"]',
                ".post-content",
                ".article-content",
                ".entry-content",
                ".content",
                "main",
            ]
            
            for selector in article_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator="\n", strip=True)
                    if len(content) > 200:
                        break
            
            # Fallback to body
            if len(content) < 200:
                body = soup.find("body")
                if body:
                    content = body.get_text(separator="\n", strip=True)
            
            # Clean up content
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            content = "\n".join(lines)
            
            # Truncate if too long
            if len(content) > 15000:
                content = content[:15000] + "...[truncated]"
            
            if len(content) < 100:
                return ToolResponse(
                    success=False,
                    error="Insufficient content extracted"
                )
            
            return ToolResponse(
                success=True,
                data={
                    "url": url,
                    "content": content,
                    "title": title,
                    "extraction_method": "FULL"
                }
            )
            
        except httpx.TimeoutException:
            return ToolResponse(success=False, error="Timeout")
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def _fetch_with_langchain(self, url: str) -> ToolResponse:
        """Fallback fetch using LangChain WebBaseLoader."""
        try:
            from langchain_community.document_loaders import WebBaseLoader
            
            loader = WebBaseLoader(
                web_paths=[url],
                requests_kwargs={"timeout": 10}  # Shorter timeout for fallback
            )
            docs = loader.load()
            
            if not docs or not docs[0].page_content:
                return ToolResponse(success=False, error="No content from LangChain loader")
            
            content = docs[0].page_content
            title = docs[0].metadata.get("title", "")
            
            if len(content) < 100:
                return ToolResponse(success=False, error="Insufficient content")
            
            return ToolResponse(
                success=True,
                data={
                    "url": url,
                    "content": content[:15000],
                    "title": title,
                    "extraction_method": "FULL"
                }
            )
        except Exception as e:
            return ToolResponse(success=False, error=f"LangChain loader failed: {str(e)}")


# ============================================================================
# Tool Registry
# ============================================================================

def get_search_tool() -> SearchTool:
    """Get configured search tool instance."""
    return SearchTool()


def get_reader_tool() -> ReaderTool:
    """Get configured reader tool instance."""
    return ReaderTool()
