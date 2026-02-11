"""
Article Generator module for the GEO/GSO Pipeline.
Generates structured GEO-ready articles and validates their structure.
"""

import re
import logging
from dataclasses import dataclass, field
from src.llm_client import LLMClient
from src.config import (
    MIN_H2_SECTIONS, MIN_FAQ_QUESTIONS, MIN_SOURCES,
    META_DESC_MIN, META_DESC_MAX, MAX_INTRO_LINES,
    MIN_TAKEAWAYS, MAX_TAKEAWAYS,
)

logger = logging.getLogger(__name__)


@dataclass
class ArticleData:
    """Structured representation of a generated article."""
    topic: str
    language: str
    tone: str
    slug: str
    title: str = ""
    meta_description: str = ""
    content_markdown: str = ""
    faq: list[dict] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    author: dict = field(default_factory=dict)
    key_takeaways: list[str] = field(default_factory=list)
    h2_count: int = 0
    intro_lines: int = 0
    validation_errors: list[str] = field(default_factory=list)


def generate_slug(topic: str) -> str:
    """Generate a URL-friendly slug from a topic string."""
    slug = topic.lower().strip()
    # Replace accented characters
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ç': 'c', 'ñ': 'n',
    }
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:80]


def _parse_title(content: str) -> str:
    """Extract the H1 title from markdown content."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _parse_meta_description(content: str) -> str:
    """Extract meta description from markdown content."""
    match = re.search(r'\*\*Meta\s*description[:\s]*\*\*\s*(.+)', content, re.IGNORECASE)
    if match:
        return match.group(1).strip().strip('[]')
    # Fallback: look for line after "Meta description"
    match = re.search(r'Meta\s*description[:\s]*(.+)', content, re.IGNORECASE)
    return match.group(1).strip().strip('[]') if match else ""


def _parse_faq(content: str) -> list[dict]:
    """Extract FAQ questions and answers from markdown content."""
    faq_list = []
    # Match patterns like "**Q: question?**\nA: answer" or "**question?**\nanswer"
    pattern = r'\*\*Q:\s*(.+?)\?\s*\*\*\s*\n\s*A:\s*(.+?)(?=\n\s*\*\*Q:|\n\s*##|\Z)'
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    for q, a in matches:
        faq_list.append({"q": q.strip() + "?", "a": a.strip()})
    
    # Fallback: try numbered format
    if not faq_list:
        pattern = r'\d+\.\s*\*\*(.+?\?)\s*\*\*\s*\n\s*(.+?)(?=\n\s*\d+\.|\n\s*##|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        for q, a in matches:
            faq_list.append({"q": q.strip(), "a": a.strip()})

    return faq_list


def _parse_sources(content: str) -> list[str]:
    """Extract source URLs from markdown content."""
    urls = re.findall(r'https?://[^\s\)]+', content)
    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        url_clean = url.rstrip('.,;:')
        if url_clean not in seen:
            seen.add(url_clean)
            unique_urls.append(url_clean)
    return unique_urls


def _parse_author(content: str) -> dict:
    """Extract author information from markdown content."""
    author = {"name": "", "bio": "", "methodology": []}
    
    # Find the author section
    author_section = re.search(
        r'(?:About the Author|Auteur).*?\n\s*\*\*(.+?)\*\*\s*[—–-]\s*(.+?)(?:\n|$)',
        content, re.IGNORECASE | re.DOTALL
    )
    if author_section:
        author["name"] = author_section.group(1).strip()
        author["bio"] = author_section.group(2).strip()
    
    # Look for additional bio lines
    bio_match = re.search(
        r'(?:About the Author|Auteur).*?\n.*?\n\n(.+?)(?:\n\s*\*\*M[ée]thodolog|$)',
        content, re.IGNORECASE | re.DOTALL
    )
    if bio_match and author["bio"]:
        extra_bio = bio_match.group(1).strip()
        if extra_bio and not extra_bio.startswith('**'):
            author["bio"] += " " + extra_bio

    return author


def _parse_takeaways(content: str) -> list[str]:
    """Extract key takeaways from the article."""
    takeaways = []
    # Find the takeaways section
    match = re.search(
        r'##\s*Key\s*Takeaways.*?\n(.*?)(?=\n##|\Z)',
        content, re.IGNORECASE | re.DOTALL
    )
    if match:
        section = match.group(1)
        items = re.findall(r'[-*]\s+(.+)', section)
        takeaways = [item.strip() for item in items if item.strip()]
    return takeaways


def _count_h2_sections(content: str) -> int:
    """Count H2 sections in the article body (excluding FAQ, Takeaways, Sources, Author)."""
    h2_matches = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
    excluded = {'faq', 'key takeaways', 'sources', 'table of contents', 'introduction',
                'about the author', 'à propos de l\'auteur', 'auteur', 'sommaire',
                'points clés', 'questions fréquentes'}
    body_h2 = [h for h in h2_matches if h.strip().lower() not in excluded]
    return len(body_h2)


def _count_intro_lines(content: str) -> int:
    """Count the number of lines in the introduction section."""
    match = re.search(
        r'##\s*Introduction\s*\n(.*?)(?=\n##)',
        content, re.IGNORECASE | re.DOTALL
    )
    if match:
        intro = match.group(1).strip()
        lines = [l for l in intro.split('\n') if l.strip()]
        return len(lines)
    return 0


class ArticleGenerator:
    """Generates and validates GEO-ready articles via LLM."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate(self, topic: str, language: str, tone: str, max_retries: int = 2, additional_context: str = "") -> ArticleData:
        """
        Generate a complete GEO-ready article for the given topic.
        Validates structure and retries if sections are missing.
        
        Args:
            topic: Article subject.
            language: Target language ('fr' or 'en').
            tone: Writing tone.
            max_retries: Max regeneration attempts if structure is invalid.
            additional_context: RAG context or real sources.
            
        Returns:
            ArticleData with parsed content and validation results.
        """
        slug = generate_slug(topic)
        
        for attempt in range(1, max_retries + 1):
            logger.info(f"Generating article for '{topic}' (attempt {attempt}/{max_retries})")
            
            raw_content = self.llm.generate_article(topic, language, tone, additional_context)
            article = self._parse_article(raw_content, topic, language, tone, slug)
            errors = self._validate(article)
            
            if not errors:
                logger.info(f"Article '{slug}' generated successfully — all sections valid")
                return article
            
            logger.warning(f"Article '{slug}' has {len(errors)} validation issues: {errors}")
            article.validation_errors = errors
            
            if attempt < max_retries:
                logger.info(f"Regenerating article '{slug}'...")
            else:
                logger.warning(f"Keeping article '{slug}' despite {len(errors)} issues (retries exhausted)")
        
        return article

    def _parse_article(self, content: str, topic: str, language: str, tone: str, slug: str) -> ArticleData:
        """Parse raw markdown content into structured ArticleData."""
        return ArticleData(
            topic=topic,
            language=language,
            tone=tone,
            slug=slug,
            title=_parse_title(content),
            meta_description=_parse_meta_description(content),
            content_markdown=content,
            faq=_parse_faq(content),
            sources=_parse_sources(content),
            author=_parse_author(content),
            key_takeaways=_parse_takeaways(content),
            h2_count=_count_h2_sections(content),
            intro_lines=_count_intro_lines(content),
        )

    def _validate(self, article: ArticleData) -> list[str]:
        """Validate article structure against GEO requirements. Returns list of errors."""
        errors = []
        
        if not article.title:
            errors.append("Missing H1 title")
        
        if not article.meta_description:
            errors.append("Missing meta description")
        elif len(article.meta_description) < META_DESC_MIN or len(article.meta_description) > META_DESC_MAX + 20:
            errors.append(f"Meta description length {len(article.meta_description)} chars (target: {META_DESC_MIN}-{META_DESC_MAX})")
        
        if article.h2_count < MIN_H2_SECTIONS:
            errors.append(f"Only {article.h2_count} H2 body sections (minimum: {MIN_H2_SECTIONS})")
        
        if len(article.faq) < MIN_FAQ_QUESTIONS:
            errors.append(f"Only {len(article.faq)} FAQ questions (minimum: {MIN_FAQ_QUESTIONS})")
        
        if len(article.sources) < MIN_SOURCES:
            errors.append(f"Only {len(article.sources)} sources (minimum: {MIN_SOURCES})")
        
        if len(article.key_takeaways) < MIN_TAKEAWAYS:
            errors.append(f"Only {len(article.key_takeaways)} takeaways (minimum: {MIN_TAKEAWAYS})")
        
        return errors
