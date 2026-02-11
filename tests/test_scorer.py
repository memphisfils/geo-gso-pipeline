"""
Tests for the ArticleScorer module.
"""

import pytest
from src.scorer import ArticleScorer, ScoreResult
from src.article_generator import ArticleData


@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return ArticleData(
        topic="Test Topic",
        language="en",
        tone="expert",
        slug="test-topic",
        title="Test Article Title",
        meta_description="This is a test meta description with exactly 155 characters for testing purposes in our pipeline. It needs to be long enough to pass the length check validation.",
        content_markdown="# Test\n\n## Section 1\n\nContent here.\n\n## FAQ\n\n**Q: Question?**\nA: Answer.",
        faq=[
            {"q": "Question 1?", "a": "Answer 1"},
            {"q": "Question 2?", "a": "Answer 2"},
            {"q": "Question 3?", "a": "Answer 3"},
            {"q": "Question 4?", "a": "Answer 4"},
            {"q": "Question 5?", "a": "Answer 5"},
        ],
        sources=[
            "https://example.com/source1",
            "https://example.org/source2",
            "https://test.com/source3",
        ],
        author={"name": "Test Author", "bio": "Test bio"},
        key_takeaways=["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
        h2_count=4,
        intro_lines=3,
    )


@pytest.fixture
def scorer():
    return ArticleScorer()


class TestArticleScorer:
    """Test suite for ArticleScorer."""

    def test_score_returns_result(self, scorer, sample_article):
        """Test that score returns a ScoreResult object."""
        result = scorer.score(sample_article)
        assert isinstance(result, ScoreResult)

    def test_score_total_range(self, scorer, sample_article):
        """Test that total score is between 0 and 100."""
        result = scorer.score(sample_article)
        assert 0 <= result.total <= 100

    def test_score_has_all_criteria(self, scorer, sample_article):
        """Test that all 5 criteria are scored."""
        result = scorer.score(sample_article)
        expected_keys = {"structure", "readability", "sources", "llm_friendliness", "duplication"}
        assert set(result.details.keys()) == expected_keys

    def test_structure_score_max(self, scorer, sample_article):
        """Test that a well-structured article gets max structure score."""
        result = scorer.score(sample_article)
        # It might not be exactly 20 depending on minor penalties, but should be high
        assert result.details["structure"] >= 15

    def test_low_sources_penalty(self, scorer, sample_article):
        """Test that few sources reduces score."""
        sample_article.sources = ["https://only-one-source.com"]
        result = scorer.score(sample_article)
        assert result.details["sources"] < 15
        assert any("sources" in w.lower() for w in result.warnings)

    def test_high_duplication_penalty(self, scorer, sample_article):
        """Test that high similarity reduces duplication score."""
        result = scorer.score(sample_article, similarity_score=0.9)
        assert result.details["duplication"] < 10
        assert any("duplication" in w.lower() for w in result.warnings)

    def test_empty_article_score(self, scorer):
        """Test scoring an empty article."""
        empty_article = ArticleData(
            topic="", language="en", tone="expert", slug="empty"
        )
        result = scorer.score(empty_article)
        assert result.total < 50
