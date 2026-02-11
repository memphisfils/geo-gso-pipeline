"""
Tests for the DeduplicationEngine module.
"""

import pytest
from src.deduplication import DeduplicationEngine, DeduplicationResult
from src.article_generator import ArticleData


@pytest.fixture
def sample_articles():
    """Create sample articles for testing."""
    return [
        ArticleData(
            topic="Topic A",
            language="en",
            tone="expert",
            slug="topic-a",
            content_markdown="# Article A\n\nThis is about machine learning and AI.",
        ),
        ArticleData(
            topic="Topic B",
            language="en",
            tone="expert",
            slug="topic-b",
            content_markdown="# Article B\n\nThis is about cooking and recipes.",
        ),
        ArticleData(
            topic="Topic C",
            language="en",
            tone="expert",
            slug="topic-c",
            content_markdown="# Article C\n\nMachine learning and artificial intelligence topics.",
        ),
    ]


@pytest.fixture
def engine():
    return DeduplicationEngine(threshold=0.85)


class TestDeduplicationEngine:
    """Test suite for DeduplicationEngine."""

    def test_analyze_returns_result(self, engine, sample_articles):
        """Test that analyze returns a DeduplicationResult."""
        result = engine.analyze(sample_articles)
        assert isinstance(result, DeduplicationResult)

    def test_single_article_no_duplicates(self, engine):
        """Test that a single article has no duplicates."""
        single = [ArticleData(topic="Test", language="en", tone="expert", slug="test", content_markdown="Content")]
        result = engine.analyze(single)
        assert len(result.duplicate_pairs) == 0
        assert result.max_similarities == [0.0]

    def test_similar_articles_detected(self, engine, sample_articles):
        """Test that similar articles are flagged."""
        result = engine.analyze(sample_articles)
        # Articles A and C should be similar (both about ML/AI)
        assert len(result.duplicate_pairs) >= 1 or any(s > 0.5 for s in result.max_similarities)

    def test_threshold_respected(self, sample_articles):
        """Test that threshold is properly stored."""
        engine = DeduplicationEngine(threshold=0.95)
        result = engine.analyze(sample_articles)
        assert result.threshold == 0.95

    def test_max_similarities_length(self, engine, sample_articles):
        """Test that max_similarities has correct length."""
        result = engine.analyze(sample_articles)
        assert len(result.max_similarities) == len(sample_articles)

    def test_empty_list_handled(self, engine):
        """Test that empty article list is handled."""
        result = engine.analyze([])
        assert len(result.duplicate_pairs) == 0
        assert result.max_similarities == []
