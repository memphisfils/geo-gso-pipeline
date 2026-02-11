"""
Exporter module for the GEO/GSO Pipeline.
Handles export of articles to Markdown, JSON, and HTML formats.
Generates the summary.json report.
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ArticleExporter:
    """Exports articles to multiple formats and generates summary reports."""

    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.articles_dir = self.output_dir / "articles"
        self.json_dir = self.output_dir / "json"
        self.html_dir = self.output_dir / "html"
        
        # Ensure directories exist
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)

    def export_markdown(self, article) -> Path:
        """
        Export article as a Markdown file.
        
        Args:
            article: ArticleData instance.
            
        Returns:
            Path to the exported file.
        """
        filepath = self.articles_dir / f"{article.slug}.md"
        filepath.write_text(article.content_markdown, encoding="utf-8")
        logger.info(f"Exported Markdown: {filepath}")
        return filepath

    def export_json(self, article, score_result) -> Path:
        """
        Export article as a publication-ready JSON file.
        
        Args:
            article: ArticleData instance.
            score_result: ScoreResult instance.
            
        Returns:
            Path to the exported file.
        """
        data = {
            "slug": article.slug,
            "title": article.title,
            "meta_description": article.meta_description,
            "content_markdown": article.content_markdown,
            "faq": article.faq,
            "sources": article.sources,
            "author": article.author,
            "score": {
                "total": score_result.total,
                "details": score_result.details,
                "warnings": score_result.warnings,
            },
            "language": article.language,
            "tone": article.tone,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        filepath = self.json_dir / f"{article.slug}.json"
        filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Exported JSON: {filepath}")
        return filepath

    def export_html(self, article, score_result) -> Path:
        """
        Export article as an HTML file with SEO meta tags (bonus feature).
        
        Args:
            article: ArticleData instance.
            score_result: ScoreResult instance.
            
        Returns:
            Path to the exported file.
        """
        # Convert markdown to basic HTML
        html_content = self._markdown_to_html(article.content_markdown)
        
        html = f"""<!DOCTYPE html>
<html lang="{article.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_escape_html(article.title)}</title>
    <meta name="description" content="{_escape_html(article.meta_description)}">
    
    <!-- Open Graph / SEO -->
    <meta property="og:title" content="{_escape_html(article.title)}">
    <meta property="og:description" content="{_escape_html(article.meta_description)}">
    <meta property="og:type" content="article">
    <meta property="og:locale" content="{'fr_FR' if article.language == 'fr' else 'en_US'}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{_escape_html(article.title)}">
    <meta name="twitter:description" content="{_escape_html(article.meta_description)}">
    
    <!-- Article Metadata -->
    <meta name="author" content="{_escape_html(article.author.get('name', ''))}">
    <meta name="quality-score" content="{score_result.total}">
    
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.7;
            color: #333;
        }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 0.5rem; }}
        h2 {{ color: #16213e; margin-top: 2rem; }}
        h3 {{ color: #0f3460; }}
        .meta-desc {{ color: #666; font-style: italic; border-left: 4px solid #e94560; padding-left: 1rem; }}
        .faq-q {{ font-weight: bold; color: #1a1a2e; }}
        .faq-a {{ margin-left: 1rem; margin-bottom: 1rem; }}
        .sources {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; }}
        .author {{ background: #eef; padding: 1.5rem; border-radius: 8px; margin-top: 2rem; }}
        .score-badge {{
            display: inline-block;
            background: {'#27ae60' if score_result.total >= 80 else '#f39c12' if score_result.total >= 60 else '#e74c3c'};
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.9rem;
        }}
        a {{ color: #e94560; }}
        ul, ol {{ padding-left: 1.5rem; }}
        blockquote {{ border-left: 4px solid #ddd; padding-left: 1rem; color: #666; }}
    </style>
</head>
<body>
    <div class="score-badge">Quality Score: {score_result.total}/100</div>
    {html_content}
</body>
</html>"""
        
        filepath = self.html_dir / f"{article.slug}.html"
        filepath.write_text(html, encoding="utf-8")
        logger.info(f"Exported HTML: {filepath}")
        return filepath

    def generate_summary(self, articles: list, scores: list, dedup_result) -> Path:
        """
        Generate the global summary.json report.
        
        Args:
            articles: List of ArticleData instances.
            scores: List of ScoreResult instances.
            dedup_result: DeduplicationResult instance.
            
        Returns:
            Path to the summary.json file.
        """
        summary = {
            "pipeline_run": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_articles": len(articles),
                "average_score": round(sum(s.total for s in scores) / len(scores), 1) if scores else 0,
            },
            "articles": [],
            "deduplication": {
                "threshold": dedup_result.threshold,
                "duplicate_pairs": dedup_result.duplicate_pairs,
                "total_duplicates_detected": len(dedup_result.duplicate_pairs),
            },
        }
        
        for article, score in zip(articles, scores):
            summary["articles"].append({
                "slug": article.slug,
                "topic": article.topic,
                "language": article.language,
                "tone": article.tone,
                "title": article.title,
                "score": {
                    "total": score.total,
                    "details": score.details,
                },
                "warnings": score.warnings,
                "validation_errors": article.validation_errors,
            })
        
        # Sort by score (highest first)
        summary["articles"].sort(key=lambda x: x["score"]["total"], reverse=True)
        
        filepath = self.output_dir / "summary.json"
        filepath.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Generated summary: {filepath}")
        return filepath

    def _markdown_to_html(self, markdown: str) -> str:
        """Basic markdown to HTML conversion without external dependencies."""
        html = markdown
        
        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Links
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', html)
        
        # Unordered lists
        html = re.sub(r'^[-*] (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>\n?)+', lambda m: f'<ul>{m.group(0)}</ul>', html)
        
        # Numbered lists  
        html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # Horizontal rules
        html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)
        
        # Paragraphs (wrap remaining text lines)
        lines = html.split('\n')
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('<'):
                result.append(f'<p>{stripped}</p>')
            else:
                result.append(line)
        html = '\n'.join(result)
        
        return html


def _escape_html(text: str) -> str:
    """Escape HTML special characters in text."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
