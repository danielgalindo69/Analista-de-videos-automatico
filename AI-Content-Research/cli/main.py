"""
CLI Interface for AI Content Research Framework.

Built with Typer and Rich.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from config.settings import get_settings
from core.models import AnalysisRequest, TaskType, Platform
from infrastructure.logging import setup_logging
from infrastructure.storage import FileStorage
from platforms.youtube import YouTubePlatform
from analysis.youtube import YouTubeTitleAnalyzer, YouTubeTrendAnalyzer

app = typer.Typer(
    name="research",
    help="AI Content Research Framework CLI",
    add_completion=False,
)
console = Console()


@app.callback()
def main():
    """Initialize logging before any subcommand runs."""
    setup_logging()


@app.command(name="info")
def show_info():
    """Display system configuration and model routing."""
    settings = get_settings()
    console.print(Panel.fit("[bold blue]AI Content Research Framework[/bold blue]", border_style="blue"))
    
    table = Table(title="System Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Ollama Host", settings.ollama.base_url)
    table.add_row("Extraction Model", settings.models.extraction_model)
    table.add_row("Reasoning Model", settings.models.reasoning_model)
    table.add_row("Browser Headless", str(settings.browser.headless))
    table.add_row("Output Directory", settings.storage.output_dir)

    console.print(table)


@app.command(name="search")
def search_youtube(
    query: str = typer.Argument(..., help="Search query (e.g. 'Five Nights at Freddy's')"),
    max_results: int = typer.Option(10, "--max", "-m", help="Maximum results to return"),
):
    """Search YouTube for videos."""
    async def _run():
        console.print(f"[bold yellow]Searching YouTube for:[/bold yellow] '{query}'...")
        platform = YouTubePlatform()
        items = await platform.search(query=query, max_results=max_results)

        table = Table(title=f"YouTube Search Results: {query}")
        table.add_column("#", style="dim")
        table.add_column("Title", style="bold white", max_width=45)
        table.add_column("Channel", style="cyan")
        table.add_column("Views", style="green")
        table.add_column("Duration", style="magenta")

        for idx, item in enumerate(items, 1):
            views = item.get_meta("view_count", 0)
            duration = item.get_meta("duration_text", "N/A")
            table.add_row(str(idx), item.title or "", item.author_name or "", f"{views:,}", duration)

        console.print(table)
        console.print(f"\n[bold green]Saved to storage![/bold green] Total: {len(items)} items.")

    asyncio.run(_run())


@app.command(name="analyze")
def analyze_query(
    query: str = typer.Argument(..., help="Topic or query to analyze (e.g. 'Five Nights at Freddy's Fear's Mind')"),
    max_results: int = typer.Option(10, "--max", "-m", help="Maximum videos to extract and analyze"),
):
    """Search YouTube and run full Title & Trend Analysis with LLMs."""
    async def _run():
        console.print(f"[bold yellow]Phase 1: Scraping YouTube for '{query}'...[/bold yellow]")
        platform = YouTubePlatform()
        items = await platform.search(query=query, max_results=max_results)

        if not items:
            console.print("[bold red]No videos extracted. Check query or connection.[/bold red]")
            return

        req = AnalysisRequest(
            query=query,
            platform=Platform.YOUTUBE,
            task_types=[TaskType.CLASSIFICATION, TaskType.TREND_ANALYSIS],
            max_items=len(items),
        )

        console.print("[bold yellow]Phase 2: Analyzing Title Patterns (Qwen3 14B)...[/bold yellow]")
        title_analyzer = YouTubeTitleAnalyzer()
        title_res = await title_analyzer.analyze(req, items)

        console.print("[bold yellow]Phase 3: Reasoning Market Trends & Opportunities (DeepSeek R1 8B)...[/bold yellow]")
        trend_analyzer = YouTubeTrendAnalyzer()
        trend_res = await trend_analyzer.analyze(req, items)

        storage = FileStorage()
        path1 = await storage.save_analysis(title_res)
        path2 = await storage.save_analysis(trend_res)

        console.print(Panel.fit("[bold green]Analysis Completed![/bold green]", border_style="green"))
        console.print(f"[cyan]Title Findings:[/cyan]\n{title_res.findings[0].description[:400]}...\n")
        console.print(f"[cyan]Trend Findings:[/cyan]\n{trend_res.findings[0].description[:400]}...\n")
        console.print(f"[bold white]Full reports saved at:[/bold white]\n- {path1}\n- {path2}")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
