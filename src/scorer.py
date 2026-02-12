"""
Scoring module for the GEO/GSO Pipeline.
Evaluates article quality across 5 criteria, each scored out of 20 (total /100).
"""

import re
import logging
from dataclasses import dataclass, field
from src.config import (
    SCORE_WEIGHTS, MIN_H2_SECTIONS, MIN_FAQ_QUESTIONS, MIN_SOURCES,
    META_DESC_MIN, META_DESC_MAX, MAX_INTRO_LINES,
    MIN_TAKEAWAYS,
)

logger = logging.getLogger(__name__)


try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    logger.warning("textstat not available — readability scoring will use fallback heuristics")


@dataclass
class ScoreResult:
    """Detailed scoring result for an article."""
    total: int = 0
    details: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _score_structure(article) -> tuple[int, list[str]]:
    """
    Score article structure (out of 20).
    Checks presence and quality of all required sections.
    """
    score = 0
    warnings = []
    max_score = SCORE_WEIGHTS["structure"]
    
    checks = {
        "H1 title": bool(article.title),
        "Meta description": bool(article.meta_description),
        "Introduction": article.intro_lines > 0,
        "Body H2 sections (≥4)": article.h2_count >= MIN_H2_SECTIONS,
        "FAQ section (≥5 Q&A)": len(article.faq) >= MIN_FAQ_QUESTIONS,
        "Key takeaways (≥5)": len(article.key_takeaways) >= MIN_TAKEAWAYS,
        "Sources (≥3)": len(article.sources) >= MIN_SOURCES,
        "Author block": bool(article.author.get("name")),
    }
    
    points_per_check = max_score / len(checks)
    
    for check_name, passed in checks.items():
        if passed:
            score += points_per_check
        else:
            warnings.append(f"Structure: missing or insufficient — {check_name}")
    
   
    if article.meta_description:
        md_len = len(article.meta_description)
        if md_len < META_DESC_MIN:
            warnings.append(f"Meta description too short ({md_len} chars, min {META_DESC_MIN})")
            score -= 1
        elif md_len > META_DESC_MAX + 20:
            warnings.append(f"Meta description too long ({md_len} chars, max ~{META_DESC_MAX})")
            score -= 1
    
    
    if article.intro_lines > MAX_INTRO_LINES:
        warnings.append(f"Introduction too long ({article.intro_lines} lines, max {MAX_INTRO_LINES})")
        score -= 1
    
    return max(0, min(int(round(score)), max_score)), warnings


def _score_readability(content: str, language: str) -> tuple[int, list[str]]:
    """
    Score readability (out of 20).
    Uses Flesch reading ease or fallback heuristics.
    """
    max_score = SCORE_WEIGHTS["readability"]
    warnings = []
    
    
    plain_text = re.sub(r'[#*\[\]\(\)`>|_-]', '', content)
    plain_text = re.sub(r'https?://\S+', '', plain_text)
    
    if TEXTSTAT_AVAILABLE:
        if language == "fr":
            
            try:
                flesch = textstat.flesch_reading_ease(plain_text)
            except Exception:
                flesch = 50  
        else:
            flesch = textstat.flesch_reading_ease(plain_text)
        

        if flesch >= 50:
            score = max_score
        elif flesch >= 30:
            score = int(max_score * 0.8)
        elif flesch >= 20:
            score = int(max_score * 0.6)
            warnings.append(f"Readability: content may be too complex (Flesch: {flesch:.0f})")
        else:
            score = int(max_score * 0.4)
            warnings.append(f"Readability: content is very difficult to read (Flesch: {flesch:.0f})")
    else:
       
        sentences = re.split(r'[.!?]+', plain_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_sentence_length <= 20:
                score = max_score
            elif avg_sentence_length <= 30:
                score = int(max_score * 0.7)
            else:
                score = int(max_score * 0.5)
                warnings.append(f"Readability: average sentence length is {avg_sentence_length:.0f} words")
        else:
            score = int(max_score * 0.5)
    
 
    list_items = len(re.findall(r'^\s*[-*]\s+', content, re.MULTILINE))
    if list_items >= 10:
        score = min(score + 2, max_score)
    
    return score, warnings


def _score_sources(sources: list[str]) -> tuple[int, list[str]]:
    """
    Score sources quality (out of 20).
    Checks count and domain diversity.
    """
    max_score = SCORE_WEIGHTS["sources"]
    warnings = []
    
    count = len(sources)
    
    if count == 0:
        warnings.append("Sources: no sources provided")
        return 0, warnings
    
    t
    if count >= 5:
        score = int(max_score * 0.7)
    elif count >= MIN_SOURCES:
        score = int(max_score * 0.5)
    else:
        score = int(max_score * 0.3)
        warnings.append(f"Sources: only {count} sources (minimum {MIN_SOURCES})")
    
   
    domains = set()
    for url in sources:
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            domains.add(match.group(1))
    
    diversity_ratio = len(domains) / count if count > 0 else 0
    if diversity_ratio >= 0.8:
        score += int(max_score * 0.3)
    elif diversity_ratio >= 0.5:
        score += int(max_score * 0.2)
    else:
        warnings.append(f"Sources: low domain diversity ({len(domains)} unique domains for {count} sources)")
        score += int(max_score * 0.1)
    
    return min(score, max_score), warnings


def _score_llm_friendliness(content: str, faq: list, takeaways: list) -> tuple[int, list[str]]:
    """
    Score LLM-friendliness (out of 20).
    Measures how well the content can be parsed by AI search engines.
    """
    max_score = SCORE_WEIGHTS["llm_friendliness"]
    warnings = []
    score = 0
    

    if len(faq) >= 5:
        score += 5
    elif len(faq) >= 3:
        score += 3
        warnings.append(f"LLM-friendliness: FAQ has only {len(faq)} questions (≥5 recommended)")
    else:
        score += 1
        warnings.append(f"LLM-friendliness: FAQ too short ({len(faq)} questions)")
    
 
    list_items = len(re.findall(r'^\s*[-*]\s+', content, re.MULTILINE))
    numbered_items = len(re.findall(r'^\s*\d+\.\s+', content, re.MULTILINE))
    total_lists = list_items + numbered_items
    if total_lists >= 15:
        score += 4
    elif total_lists >= 8:
        score += 3
    elif total_lists >= 3:
        score += 2
    else:
        score += 1
        warnings.append("LLM-friendliness: low use of lists/enumerations")
    
  
    bold_terms = len(re.findall(r'\*\*[^*]+\*\*', content))
    if bold_terms >= 10:
        score += 3
    elif bold_terms >= 5:
        score += 2
    else:
        score += 1
        warnings.append("LLM-friendliness: few bold/highlighted terms")
    
   
    if len(takeaways) >= MIN_TAKEAWAYS:
        score += 3
    elif len(takeaways) >= 3:
        score += 2
    else:
        score += 1
    

    h2_sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
    if len(h2_sections) > 1:
        section_lengths = [len(s.split()) for s in h2_sections[1:]]
        avg_length = sum(section_lengths) / len(section_lengths)
        if 50 <= avg_length <= 300:
            score += 3  
        elif 30 <= avg_length <= 500:
            score += 2
        else:
            score += 1
            warnings.append(f"LLM-friendliness: uneven section sizes (avg {avg_length:.0f} words)")
    else:
        score += 1
    

    entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
    unique_entities = len(set(entities))
    if unique_entities >= 15:
        score += 2
    elif unique_entities >= 5:
        score += 1
    
    return min(score, max_score), warnings


class ArticleScorer:
    """Evaluates article quality across multiple criteria."""

    def score(self, article, similarity_score: float = 0.0) -> ScoreResult:
        """
        Score an article on 5 criteria (each /20, total /100).
        
        Args:
            article: ArticleData instance.
            similarity_score: Max similarity with other articles (0-1).
            
        Returns:
            ScoreResult with total, details, and warnings.
        """
        result = ScoreResult()
        
        # 1. Structure
        s_struct, w_struct = _score_structure(article)
        result.details["structure"] = s_struct
        result.warnings.extend(w_struct)
        
        # 2. Readability
        s_read, w_read = _score_readability(article.content_markdown, article.language)
        result.details["readability"] = s_read
        result.warnings.extend(w_read)
        
        # 3. Sources
        s_sources, w_sources = _score_sources(article.sources)
        result.details["sources"] = s_sources
        result.warnings.extend(w_sources)
        
        # 4. LLM-friendliness
        s_llm, w_llm = _score_llm_friendliness(
            article.content_markdown, article.faq, article.key_takeaways
        )
        result.details["llm_friendliness"] = s_llm
        result.warnings.extend(w_llm)
        
      
        max_dup = SCORE_WEIGHTS["duplication"]
        if similarity_score <= 0.3:
            s_dup = max_dup
        elif similarity_score <= 0.5:
            s_dup = int(max_dup * 0.8)
        elif similarity_score <= 0.7:
            s_dup = int(max_dup * 0.6)
        elif similarity_score <= 0.85:
            s_dup = int(max_dup * 0.4)
            result.warnings.append(f"Duplication risk: high similarity ({similarity_score:.2f}) with another article")
        else:
            s_dup = int(max_dup * 0.1)
            result.warnings.append(f"Duplication risk: VERY HIGH similarity ({similarity_score:.2f}) — content may be duplicate")
        result.details["duplication"] = s_dup
        
        # Total
        result.total = sum(result.details.values())
        
        logger.info(f"Article scored: {result.total}/100 — {result.details}")
        if result.warnings:
            logger.info(f"Warnings: {result.warnings}")
        
        return result
