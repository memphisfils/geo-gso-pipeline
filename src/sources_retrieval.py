"""
Sources Retrieval module for the GEO/GSO Pipeline.
Fetches and validates real sources from the web.
"""

import re
import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, quote_plus
import time
import os

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """Represents a retrieved source."""
    url: str
    title: str
    snippet: str
    domain: str
    is_accessible: bool = True
    relevance_score: float = 0.0


class WebSearchClient:
    """
    Web search client for retrieving relevant sources.
    Supports multiple search providers.
    """
    
    def __init__(self, provider: str = "duckduckgo", api_key: str = None):
        """
        Initialize the search client.
        
        Args:
            provider: Search provider ('duckduckgo', 'serper', 'tavily').
            api_key: API key for paid providers.
        """
        self.provider = provider
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; GEO-GSO-Pipeline/1.0)"
        })
    
    def search(self, query: str, num_results: int = 10) -> List[Source]:
        """
        Search the web for relevant sources.
        
        Args:
            query: Search query.
            num_results: Maximum number of results.
            
        Returns:
            List of Source objects.
        """
        if self.provider == "duckduckgo":
            return self._search_duckduckgo(query, num_results)
        elif self.provider == "serper":
            return self._search_serper(query, num_results)
        elif self.provider == "tavily":
            return self._search_tavily(query, num_results)
        else:
            logger.warning(f"Unknown provider: {self.provider}")
            return []
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Source]:
        """Search using DuckDuckGo (free, no API key required)."""
        sources = []
        
        try:
            # Use DuckDuckGo HTML version for scraping
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = self.session.get(url, timeout=15)
            # 403 Forbidden is common with DDG scraping, handle gracefully
            if response.status_code == 403:
                logger.warning("DuckDuckGo blocked request (403). Try using a paid provider.")
                return []
            
            response.raise_for_status()
            
            # Parse results
            result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(result_pattern, response.text)
            
            for i, (url, title) in enumerate(matches[:num_results]):
                # DuckDuckGo uses redirect URLs, extract actual URL
                if "uddg=" in url:
                    try:
                        actual_url = url.split("uddg=")[-1].split("&")[0]
                        from urllib.parse import unquote
                        actual_url = unquote(actual_url)
                    except:
                        actual_url = url
                else:
                    actual_url = url
                
                domain = urlparse(actual_url).netloc
                
                sources.append(Source(
                    url=actual_url,
                    title=title.strip(),
                    snippet="",  
                    domain=domain,
                    is_accessible=True,
                ))
            
            logger.info(f"DuckDuckGo search found {len(sources)} results for: {query}")
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
        
        return sources
    
    def _search_serper(self, query: str, num_results: int) -> List[Source]:
        """Search using Serper.dev API (requires API key)."""
        if not self.api_key:
            logger.warning("Serper API key not provided")
            return []
        
        sources = []
        
        try:
            response = self.session.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": self.api_key},
                json={"q": query, "num": num_results},
                timeout=15,
            )
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get("organic", []):
                sources.append(Source(
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    domain=urlparse(item.get("link", "")).netloc,
                    is_accessible=True,
                ))
            
            logger.info(f"Serper search found {len(sources)} results")
            
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
        
        return sources
    
    def _search_tavily(self, query: str, num_results: int) -> List[Source]:
        """Search using Tavily API (requires API key)."""
        if not self.api_key:
            logger.warning("Tavily API key not provided")
            return []
        
        sources = []
        
        try:
            response = self.session.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": query,
                    "max_results": num_results,
                    "include_raw_content": False,
                },
                timeout=30,
            )
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get("results", []):
                sources.append(Source(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("content", ""),
                    domain=urlparse(item.get("url", "")).netloc,
                    is_accessible=True,
                ))
            
            logger.info(f"Tavily search found {len(sources)} results")
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
        
        return sources


class SourceValidator:
    """Validates and enriches source URLs."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; GEO-GSO-Pipeline/1.0)"
        })
    
    def validate_url(self, url: str) -> Dict:
        """
        Validate a URL by making a HEAD request.
        
        Returns:
            Dict with 'is_valid', 'status_code', 'content_type'.
        """
        try:
            
            try:
                response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            except requests.MethodNotAllowed:
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.close()
                
            return {
                "is_valid": response.status_code < 400,
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "final_url": response.url,
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
            }
    
    def batch_validate(self, urls: List[str], delay: float = 0.5) -> List[Dict]:
        """Validate multiple URLs with rate limiting."""
        results = []
        
        for url in urls:
            results.append({
                "url": url,
                **self.validate_url(url)
            })
            time.sleep(delay) 
        
        return results


class SourcesRetrievalEngine:
    """
    Main engine for retrieving and managing sources.
    """
    
    def __init__(self, search_provider: str = "duckduckgo", api_key: str = None):
        self.search_client = WebSearchClient(provider=search_provider, api_key=api_key)
        self.validator = SourceValidator()
    
    def get_sources_for_topic(self, topic: str, num_sources: int = 5) -> List[Source]:
        """
        Retrieve relevant sources for a topic.
        
        Args:
            topic: The article topic.
            num_sources: Number of sources to retrieve.
            
        Returns:
            List of validated Source objects.
        """
        
        queries = self._generate_search_queries(topic)
        
        all_sources = []
        for query in queries:
            sources = self.search_client.search(query, num_results=num_sources)
            all_sources.extend(sources)
        
       
        seen_urls = set()
        unique_sources = []
        for source in all_sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        # Validate top sources
        validated = []
        for source in unique_sources[:num_sources * 2]:
            validation = self.validator.validate_url(source.url)
            if validation.get("is_valid"):
                source.is_accessible = True
                validated.append(source)
            
            if len(validated) >= num_sources:
                break
        
        logger.info(f"Retrieved {len(validated)} valid sources for: {topic}")
        return validated
    
    def _generate_search_queries(self, topic: str) -> List[str]:
        """Generate multiple search queries from a topic."""
        queries = [
            topic,  
            f"{topic} guide 2024 2025",  # Time-specific
            f"best {topic}",  # Best/recommendations
        ]
        return queries
    
    def format_sources_for_article(self, sources: List[Source]) -> str:
        """Format sources as markdown for article inclusion."""
        lines = ["## Sources\n"]
        
        for i, source in enumerate(sources, 1):
            lines.append(f"{i}. [{source.title}]({source.url}) — {source.snippet[:100]}...")
        
        return "\n".join(lines)


def enrich_article_with_sources(topic: str, num_sources: int = 5) -> List[str]:
    """
    Enrich an article with real, validated sources.
    
    Args:
        topic: The article topic.
        num_sources: Number of sources to add.
        
    Returns:
        List of source URLs.
    """
    # Check for API key
    api_key = os.getenv("SERPER_API_KEY") or os.getenv("TAVILY_API_KEY")
    provider = "serper" if os.getenv("SERPER_API_KEY") else ("tavily" if os.getenv("TAVILY_API_KEY") else "duckduckgo")
    
    engine = SourcesRetrievalEngine(
        search_provider=provider,
        api_key=api_key,
    )
    
    sources = engine.get_sources_for_topic(topic, num_sources)
    
    return [s.url for s in sources if s.is_accessible]
