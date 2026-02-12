"""
Anti-Duplication module for the GEO/GSO Pipeline.
Uses sentence-transformers embeddings + cosine similarity to detect duplicate content.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from src.config import SIMILARITY_THRESHOLD, EMBEDDING_MODEL

logger = logging.getLogger(__name__)


_model = None


def _get_model():
    """Lazy-load the sentence-transformers model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
    return _model


@dataclass
class DeduplicationResult:
    """Results of the deduplication analysis."""
    similarity_matrix: list[list[float]] = field(default_factory=list)
    duplicate_pairs: list[dict] = field(default_factory=list)
    max_similarities: list[float] = field(default_factory=list)
    threshold: float = SIMILARITY_THRESHOLD


class DeduplicationEngine:
    """Detects duplicate content across generated articles using embeddings."""

    def __init__(self, threshold: float = None):
        self.threshold = threshold or SIMILARITY_THRESHOLD

    def analyze(self, articles: list) -> DeduplicationResult:
        """
        Compute similarity matrix across all articles and detect duplicates.
        
        Args:
            articles: List of ArticleData instances.
            
        Returns:
            DeduplicationResult with similarity matrix, duplicate pairs, and per-article max similarity.
        """
        if len(articles) < 2:
            logger.info("Less than 2 articles — skipping deduplication")
            return DeduplicationResult(
                max_similarities=[0.0] * len(articles),
                threshold=self.threshold,
            )

        logger.info(f"Computing embeddings for {len(articles)} articles...")
        
        model = _get_model()
        
        # Use article content for embedding (first 1000 chars to keep it manageable)
        texts = [a.content_markdown[:2000] for a in articles]
        embeddings = model.encode(texts, show_progress_bar=False)
        
        # Compute cosine similarity matrix
        from sklearn.metrics.pairwise import cosine_similarity
        sim_matrix = cosine_similarity(embeddings)
        
        result = DeduplicationResult(
            similarity_matrix=sim_matrix.tolist(),
            threshold=self.threshold,
        )
        
        # Find duplicate pairs
        n = len(articles)
        max_sims = [0.0] * n
        
        for i in range(n):
            for j in range(i + 1, n):
                sim = sim_matrix[i][j]
                max_sims[i] = max(max_sims[i], sim)
                max_sims[j] = max(max_sims[j], sim)
                
                if sim > self.threshold:
                    pair = {
                        "article_1": articles[i].slug,
                        "article_2": articles[j].slug,
                        "similarity": round(float(sim), 4),
                        "status": "REJECTED" if sim > self.threshold else "OK",
                    }
                    result.duplicate_pairs.append(pair)
                    logger.warning(
                        f"Duplicate detected: '{articles[i].slug}' ↔ '{articles[j].slug}' "
                        f"(similarity: {sim:.4f}, threshold: {self.threshold})"
                    )
        
        result.max_similarities = [round(float(s), 4) for s in max_sims]
        
        logger.info(
            f"Deduplication complete — {len(result.duplicate_pairs)} duplicate pair(s) found "
            f"(threshold: {self.threshold})"
        )
        
        return result
