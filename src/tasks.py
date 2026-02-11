"""
Celery tasks for async article generation.
Enables distributed processing and job queues.
"""

import logging
from typing import Dict, Any, Optional

try:
    from celery import Celery, shared_task
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    # Mock decorator if celery not available
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class Celery:
        def __init__(self, *args, **kwargs):
            self.conf = {}
        def config_from_object(self, *args): pass


logger = logging.getLogger(__name__)

# Celery app configuration
if HAS_CELERY:
    app = Celery('geo_gso_pipeline')
    try:
        app.config_from_object('celeryconfig')
    except ImportError:
        logger.warning("celeryconfig module not found, using default settings")
else:
    app = None


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_article_task(self, topic_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Async task to generate a single article.
    
    Args:
        topic_data: Dict with 'topic', 'language', 'tone' keys.
        
    Returns:
        Dict with article slug and status.
    """
    try:
        from src.llm_client import LLMClient
        from src.article_generator import ArticleGenerator
        
        logger.info(f"Starting generation for: {topic_data['topic']}")
        
        llm = LLMClient()
        generator = ArticleGenerator(llm)
        
        article = generator.generate(
            topic=topic_data["topic"],
            language=topic_data.get("language", "en"),
            tone=topic_data.get("tone", "expert"),
        )
        
        logger.info(f"Completed generation: {article.slug}")
        
        return {
            "success": True,
            "slug": article.slug,
            "title": article.title,
            "topic": topic_data["topic"],
        }
        
    except Exception as e:
        logger.error(f"Task failed for {topic_data['topic']}: {e}")
        if HAS_CELERY:
            self.retry(exc=e)
        return {"success": False, "error": str(e), "topic": topic_data["topic"]}


@shared_task
def score_article_task(article_data: Dict) -> Dict[str, Any]:
    """
    Async task to score an article.
    
    Args:
        article_data: Serialized ArticleData dict.
        
    Returns:
        Dict with score results.
    """
    from src.scorer import ArticleScorer
    from src.article_generator import ArticleData
    
    article = ArticleData(**article_data)
    scorer = ArticleScorer()
    result = scorer.score(article)
    
    return {
        "slug": article.slug,
        "total": result.total,
        "details": result.details,
        "warnings": result.warnings,
    }


@shared_task
def export_article_task(article_data: Dict, score_data: Dict, output_dir: str) -> Dict[str, Any]:
    """
    Async task to export an article.
    
    Args:
        article_data: Serialized ArticleData dict.
        score_data: Serialized ScoreResult dict.
        output_dir: Output directory path.
        
    Returns:
        Dict with export paths.
    """
    from src.exporter import ArticleExporter
    from src.article_generator import ArticleData
    from src.scorer import ScoreResult
    
    article = ArticleData(**article_data)
    score = ScoreResult(**score_data)
    
    exporter = ArticleExporter(output_dir)
    
    md_path = exporter.export_markdown(article)
    json_path = exporter.export_json(article, score)
    html_path = exporter.export_html(article, score)
    
    return {
        "slug": article.slug,
        "markdown": str(md_path),
        "json": str(json_path),
        "html": str(html_path),
    }


# Alternative: Simple batch processing without Celery broker
class BatchProcessor:
    """
    Simple batch processor using multiprocessing.
    No external broker required.
    """
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
    
    def process_batch(self, topics: list, output_dir: str) -> dict:
        """
        Process multiple topics in parallel using multiprocessing.
        
        Args:
            topics: List of topic dicts.
            output_dir: Output directory path.
            
        Returns:
            Processing summary.
        """
        from multiprocessing import Pool
        from functools import partial
        
        # Windows multiprocessing requires this check usually, but here it's called inside a function
        # We need to make sure _process_single is picklable. It is a method, so we should use staticmethod or separate function.
        # But 'partial' might work if we are careful.
        
        process_func = partial(self._process_single, output_dir=output_dir)
        
        with Pool(self.max_workers) as pool:
            results = pool.map(process_func, topics)
        
        return {
            "total": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success")),
            "results": results,
        }
    
    @staticmethod
    def _process_single(topic_data: dict, output_dir: str) -> dict:
        """Process a single topic (runs in separate process)."""
        try:
            # Re-import inside process to avoid pickling issues
            from src.llm_client import LLMClient
            from src.article_generator import ArticleGenerator
            from src.scorer import ArticleScorer
            from src.exporter import ArticleExporter
            
            # Need strict error handling here
            try:
                llm = LLMClient()
                generator = ArticleGenerator(llm)
                scorer = ArticleScorer()
                exporter = ArticleExporter(output_dir)
                
                # Check required keys
                if "topic" not in topic_data:
                    return {"success": False, "error": "Missing topic key", "topic_data": topic_data}
                
                article = generator.generate(
                    topic=topic_data["topic"],
                    language=topic_data.get("language", "en"),
                    tone=topic_data.get("tone", "expert"),
                )
                
                score = scorer.score(article)
                
                exporter.export_markdown(article)
                exporter.export_json(article, score)
                exporter.export_html(article, score)
                
                return {
                    "success": True,
                    "slug": article.slug,
                    "score": score.total,
                }
            except Exception as e:
                return {
                    "success": False,
                    "topic": topic_data.get("topic", "unknown"),
                    "error": str(e),
                }
                
        except ImportError as e:
            return {
                "success": False,
                "topic": topic_data.get("topic", "unknown"),
                "error": f"Import error in worker: {e}",
            }
