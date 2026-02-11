"""
GEO/GSO Pipeline — CLI Entrypoint
Generates GEO-ready articles from topics with scoring, anti-duplication, and publication-ready export.

Usage:
    python generate.py --input topics.json --output ./out
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler

# ── Setup Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
logger = logging.getLogger("geo_gso_pipeline")
console = Console()


def load_topics(input_path: str) -> list[dict]:
    """Load and validate topics from JSON file."""
    path = Path(input_path)
    if not path.exists():
        console.print(f"[red]Error: Input file '{input_path}' not found[/red]")
        sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        topics = json.load(f)
    
    if not isinstance(topics, list) or len(topics) == 0:
        console.print("[red]Error: topics.json must be a non-empty JSON array[/red]")
        sys.exit(1)
    
    # Validate each topic
    for i, topic in enumerate(topics):
        if "topic" not in topic:
            console.print(f"[red]Error: Topic #{i+1} is missing 'topic' field[/red]")
            sys.exit(1)
        topic.setdefault("language", "en")
        topic.setdefault("tone", "expert")
    
    return topics


def run_pipeline(input_path: str, output_dir: str, parallel: bool = False):
    """
    Main pipeline orchestration:
    1. Load topics
    2. Generate articles via LLM  
    3. Score quality
    4. Run deduplication
    5. Export (Markdown + JSON + HTML)
    6. Generate summary
    """
    from src.config import validate_config
    from src.llm_client import LLMClient
    from src.article_generator import ArticleGenerator
    from src.scorer import ArticleScorer
    from src.deduplication import DeduplicationEngine
    from src.exporter import ArticleExporter

    # ── Validation ─────────────────────────────────────────────────
    console.print(Panel.fit(
        "[bold cyan]🚀 GEO/GSO Pipeline — Article Generation & Scoring[/bold cyan]",
        border_style="cyan",
    ))
    
    config_errors = validate_config()
    if config_errors:
        for err in config_errors:
            console.print(f"[red]Config Error: {err}[/red]")
        sys.exit(1)
    
    # ── Load Topics ────────────────────────────────────────────────
    topics = load_topics(input_path)
    console.print(f"\n[green]✓[/green] Loaded [bold]{len(topics)}[/bold] topics from [cyan]{input_path}[/cyan]")
    
    # ── Initialize Modules ─────────────────────────────────────────
    llm_client = LLMClient()
    generator = ArticleGenerator(llm_client)
    scorer = ArticleScorer()
    dedup_engine = DeduplicationEngine()
    exporter = ArticleExporter(output_dir)
    
    # ── Step 1: Generate Articles ──────────────────────────────────
    articles = []
    console.print(f"\n[bold]📝 Step 1/4: Generating articles...[/bold]\n")
    
    if parallel and len(topics) > 1:
        # Parallel generation (bonus feature)
        max_workers = min(3, len(topics))  # Limit to avoid rate limits
        console.print(f"  Using parallel processing ({max_workers} workers)\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, topic_data in enumerate(topics):
                future = executor.submit(
                    generator.generate,
                    topic_data["topic"],
                    topic_data["language"],
                    topic_data["tone"],
                )
                futures[future] = (i, topic_data)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Generating articles...", total=len(topics))
                
                results = [None] * len(topics)
                for future in as_completed(futures):
                    idx, topic_data = futures[future]
                    try:
                        article = future.result()
                        results[idx] = article
                        progress.update(task, advance=1, description=f"✓ {article.slug}")
                    except Exception as e:
                        logger.error(f"Failed to generate article for '{topic_data['topic']}': {e}")
                        progress.update(task, advance=1, description=f"✗ {topic_data['topic']}")
                
                articles = [a for a in results if a is not None]
    else:
        # Sequential generation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Generating articles...", total=len(topics))
            
            for i, topic_data in enumerate(topics):
                try:
                    progress.update(
                        task,
                        description=f"[{i+1}/{len(topics)}] {topic_data['topic'][:50]}..."
                    )
                    article = generator.generate(
                        topic_data["topic"],
                        topic_data["language"],
                        topic_data["tone"],
                    )
                    articles.append(article)
                    progress.update(task, advance=1)
                except Exception as e:
                    logger.error(f"Failed to generate article for '{topic_data['topic']}': {e}")
                    progress.update(task, advance=1)
    
    if not articles:
        console.print("[red]Error: No articles were generated. Check your API key and connection.[/red]")
        sys.exit(1)
    
    console.print(f"[green]✓[/green] Generated [bold]{len(articles)}[/bold] articles\n")
    
    # ── Step 2: Deduplication ──────────────────────────────────────
    console.print(f"[bold]🔍 Step 2/4: Running deduplication analysis...[/bold]\n")
    dedup_result = dedup_engine.analyze(articles)
    
    if dedup_result.duplicate_pairs:
        console.print(f"[yellow]⚠ {len(dedup_result.duplicate_pairs)} duplicate pair(s) detected![/yellow]")
        for pair in dedup_result.duplicate_pairs:
            console.print(f"  • {pair['article_1']} ↔ {pair['article_2']} (similarity: {pair['similarity']:.4f})")
    else:
        console.print(f"[green]✓[/green] No duplicates detected (threshold: {dedup_result.threshold})")
    
    # ── Step 3: Scoring ────────────────────────────────────────────
    console.print(f"\n[bold]📊 Step 3/4: Scoring articles...[/bold]\n")
    scores = []
    
    for i, article in enumerate(articles):
        max_sim = dedup_result.max_similarities[i] if i < len(dedup_result.max_similarities) else 0.0
        score = scorer.score(article, similarity_score=max_sim)
        scores.append(score)
    
    # Display scores table
    score_table = Table(title="Article Quality Scores", show_lines=True)
    score_table.add_column("Article", style="cyan", min_width=30)
    score_table.add_column("Score", justify="center", style="bold")
    score_table.add_column("Structure", justify="center")
    score_table.add_column("Readability", justify="center")
    score_table.add_column("Sources", justify="center")
    score_table.add_column("LLM-Friendly", justify="center")
    score_table.add_column("Dedup", justify="center")
    score_table.add_column("Warnings", justify="center")
    
    for article, score in zip(articles, scores):
        d = score.details
        total_str = f"[{'green' if score.total >= 80 else 'yellow' if score.total >= 60 else 'red'}]{score.total}/100[/]"
        score_table.add_row(
            article.slug[:35],
            total_str,
            str(d.get("structure", 0)),
            str(d.get("readability", 0)),
            str(d.get("sources", 0)),
            str(d.get("llm_friendliness", 0)),
            str(d.get("duplication", 0)),
            str(len(score.warnings)),
        )
    
    console.print(score_table)
    
    # ── Step 4: Export ─────────────────────────────────────────────
    console.print(f"\n[bold]💾 Step 4/4: Exporting articles...[/bold]\n")
    
    for article, score in zip(articles, scores):
        exporter.export_markdown(article)
        exporter.export_json(article, score)
        exporter.export_html(article, score)
    
    # Generate global summary
    summary_path = exporter.generate_summary(articles, scores, dedup_result)
    
    console.print(f"[green]✓[/green] Exported {len(articles)} articles:")
    console.print(f"  📄 Markdown: {exporter.articles_dir}")
    console.print(f"  📋 JSON:     {exporter.json_dir}")
    console.print(f"  🌐 HTML:     {exporter.html_dir}")
    console.print(f"  📊 Summary:  {summary_path}")
    
    # ── Final Summary ──────────────────────────────────────────────
    avg_score = sum(s.total for s in scores) / len(scores)
    console.print(Panel.fit(
        f"[bold green]✅ Pipeline complete![/bold green]\n\n"
        f"  Articles generated: [bold]{len(articles)}[/bold]\n"
        f"  Average score:      [bold]{avg_score:.1f}/100[/bold]\n"
        f"  Duplicates found:   [bold]{len(dedup_result.duplicate_pairs)}[/bold]\n"
        f"  Output directory:   [cyan]{output_dir}[/cyan]",
        border_style="green",
        title="Pipeline Summary",
    ))


def main():
    parser = argparse.ArgumentParser(
        description="GEO/GSO Pipeline — Generate GEO-ready articles with quality scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py --input topics.json --output ./out
  python generate.py --input topics.json --output ./out --parallel
        """,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the topics.json input file",
    )
    parser.add_argument(
        "--output", "-o",
        default="./out",
        help="Output directory (default: ./out)",
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Enable parallel article generation (bonus feature)",
    )
    
    args = parser.parse_args()
    run_pipeline(args.input, args.output, parallel=args.parallel)


if __name__ == "__main__":
    main()
