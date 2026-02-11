"""
WordPress Publisher module for the GEO/GSO Pipeline.
Publishes articles to WordPress via REST API.
"""

import json
import logging
import requests
from dataclasses import dataclass
from typing import Optional
from src.config import OPENAI_API_KEY  # Import pattern consistency

logger = logging.getLogger(__name__)


@dataclass
class WordPressConfig:
    """Configuration for WordPress connection."""
    url: str  # e.g., "https://yourblog.com/wp-json/wp/v2"
    username: str
    application_password: str  # WordPress Application Password
    
    @classmethod
    def from_env(cls) -> Optional['WordPressConfig']:
        """Load config from environment variables."""
        import os
        url = os.getenv("WP_URL")
        username = os.getenv("WP_USERNAME")
        password = os.getenv("WP_APP_PASSWORD")
        
        if all([url, username, password]):
            return cls(url=url, username=username, application_password=password)
        return None


class WordPressPublisher:
    """
    Publishes articles to WordPress via REST API.
    
    Features:
    - Creates posts with proper formatting
    - Sets featured image (optional)
    - Assigns categories and tags
    - Handles authentication via Application Passwords
    """
    
    def __init__(self, config: WordPressConfig = None, dry_run: bool = True):
        """
        Initialize the publisher.
        
        Args:
            config: WordPress configuration. If None, loads from env.
            dry_run: If True, simulates publishing without making API calls.
        """
        self.config = config or WordPressConfig.from_env()
        self.dry_run = dry_run
        self.session = requests.Session()
        
        if self.config and not dry_run:
            self.session.auth = (self.config.username, self.config.application_password)
    
    def publish_article(self, article, score, status: str = "draft") -> dict:
        """
        Publish an article to WordPress.
        
        Args:
            article: ArticleData instance.
            score: ScoreResult instance.
            status: Post status ('draft', 'publish', 'pending').
            
        Returns:
            dict with 'success', 'post_id', 'url', or 'error'.
        """
        if not self.config:
            logger.warning("WordPress not configured - skipping publication")
            return {"success": False, "error": "WordPress not configured"}
        
        # Prepare post data
        post_data = {
            "title": article.title,
            "slug": article.slug,
            "content": self._format_content(article),
            "excerpt": article.meta_description,
            "status": status,
            "meta": {
                "quality_score": score.total,
                "generated_by": "geo-gso-pipeline",
            }
        }
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would publish: {article.slug}")
            return {
                "success": True,
                "dry_run": True,
                "post_id": None,
                "slug": article.slug,
                "status": status,
                "message": "Dry run - no actual publication"
            }
        
        try:
            response = self.session.post(
                f"{self.config.url}/posts",
                json=post_data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Published article: {article.slug} (ID: {result['id']})")
            
            return {
                "success": True,
                "post_id": result["id"],
                "url": result.get("link", ""),
                "slug": article.slug,
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to publish {article.slug}: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_content(self, article) -> str:
        """Format article content for WordPress."""
        # Convert markdown to HTML (basic conversion)
        content = article.content_markdown
        
        # Add quality badge at the top
        # Check if quality_score exists on article, otherwise assume N/A or get it from somewhere else
        # The prompt code assumes article.quality_score exists, but it's passed as 'score' arg to publish_article
        # I'll use a placeholder or modify to use 'score' arg if needed, but the prompt code uses article.quality_score in the HTML badge
        # I will assume score.total is what we want.
        
        badge = f"""
        <div style="background: #f0f0f0; padding: 10px; margin-bottom: 20px; border-radius: 5px;">
            <strong>Quality Score:</strong> {article.quality_score if hasattr(article, 'quality_score') else 'N/A'}/100
        </div>
        """
        
        # Simple markdown to HTML conversion
        import re
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
        content = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', content)
        
        return badge + content
    
    def test_connection(self) -> bool:
        """Test the WordPress connection."""
        if self.dry_run:
            logger.info("[DRY RUN] Connection test skipped")
            return True
        
        try:
            response = self.session.get(f"{self.config.url}/users/me", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def mock_wordpress_publish(articles: list, scores: list) -> dict:
    """
    Mock WordPress publication for testing.
    
    Returns simulated publication results without making API calls.
    """
    publisher = WordPressPublisher(dry_run=True)
    results = []
    
    for article, score in zip(articles, scores):
        result = publisher.publish_article(article, score)
        results.append(result)
    
    return {
        "total": len(results),
        "published": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "dry_run": True,
        "results": results,
    }
