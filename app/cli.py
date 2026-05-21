"""CLI entry point — github-radar command line interface."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from github_radar.models.config import Settings
from github_radar.models.repo import RepoRef
from github_radar.discover.github_search import search_to_refs, search_repos
from github_radar.discover.scoring import score_candidates

app = typer.Typer(
    name="github-radar",
    help="GitHub → Obsidian research pipeline",
    no_args_is_help=True,
)
console = Console()


def _get_settings() -> Settings:
    return Settings()


@app.command()
def analyze_repo(
    repo: str = typer.Argument(..., help="owner/repo or GitHub URL"),
    force: bool = typer.Option(False, "--force", "-f", help="Re-run all phases"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Fetch only, skip LLM analysis"),
):
    """Analyze a single GitHub repository."""
    from app.task_runner import run_repo_analysis
    settings = _get_settings()

    try:
        ref = RepoRef.parse(repo)
        console.print(f"[bold]Analyzing[/bold] {ref.full_name} ...")
        task_id = run_repo_analysis(repo, settings=settings, force=force)
        console.print(f"[green]✓[/green] Analysis complete. Task: {task_id}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def search_topic(
    query: str = typer.Argument(..., help="Search query or topic"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
    analyze: int = typer.Option(0, "--analyze", "-a", help="Deep-analyze top N results"),
):
    """Search GitHub for a topic and list candidates."""
    from app.task_runner import run_repo_analysis
    settings = _get_settings()

    console.print(f"[bold]Searching[/bold] '{query}' ...")
    items = search_repos(query, token=settings.github_token, per_page=limit)
    scored = score_candidates(items)

    table = Table(title=f"Results for '{query}'")
    table.add_column("#", style="dim")
    table.add_column("Repo")
    table.add_column("Stars")
    table.add_column("Score", justify="right")

    from github_radar.discover.scoring import format_score
    for i, entry in enumerate(scored[:limit], 1):
        table.add_row(
            str(i),
            entry["full_name"],
            str(entry.get("stars", "?")),
            format_score(entry),
        )

    console.print(table)

    if analyze > 0:
        console.print(f"\n[bold]Deep-analyzing top {analyze}...[/bold]")
        for entry in scored[:analyze]:
            name = entry["full_name"]
            console.print(f"\n--- {name} ---")
            try:
                run_repo_analysis(name, settings=settings)
            except Exception as e:
                console.print(f"[red]Failed:[/red] {e}")


@app.command()
def resume(
    task_id: str = typer.Argument(..., help="Task ID to resume"),
):
    """Resume an interrupted task."""
    from app.task_runner import resume_analysis
    settings = _get_settings()

    console.print(f"[bold]Resuming[/bold] {task_id} ...")
    try:
        resume_analysis(task_id, settings=settings)
        console.print("[green]✓[/green] Task resumed and completed.")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def daily(
    since: str = typer.Option("daily", "--since", help="daily, weekly, or monthly"),
    max_analyze: int = typer.Option(3, "--max-analyze", "-m", help="Max repos to deep-analyze"),
):
    """Run the daily discovery + analysis pipeline."""
    from app.scheduler import run_daily
    settings = _get_settings()
    result = run_daily(settings=settings, max_analyze=max_analyze, since=since)
    console.print(f"\n[green]✓[/green] Daily digest complete: {result['digest_note']}")


@app.command()
def list_repos(
    topic: str = typer.Option(None, "--topic", "-t", help="Filter by topic"),
):
    """List indexed repos from the knowledge base."""
    from github_radar.discover.retrieval import KnowledgeBase
    kb = KnowledgeBase(_get_settings())
    repos = kb.search(topic) if topic else kb.list_repos()
    if not repos:
        console.print("[dim]No repos indexed yet.[/dim]")
        return
    table = Table(title="Indexed Repos")
    table.add_column("Repo")
    table.add_column("Stars")
    table.add_column("Language")
    table.add_column("Topics")
    for r in repos[:50]:
        table.add_row(
            r.get("repo", "?"),
            str(r.get("stars", "?")),
            r.get("language", "?"),
            ", ".join(r.get("topics", [])[:4]),
        )
    console.print(table)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (topic or keyword)"),
):
    """Search the indexed knowledge base."""
    from github_radar.discover.retrieval import KnowledgeBase
    kb = KnowledgeBase(_get_settings())
    results = kb.search(query)
    if not results:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        return
    for r in results:
        console.print(f"  [{r.get('language', '?')}] {r['repo']} ⭐{r.get('stars', '?')}")
        console.print(f"    Topics: {', '.join(r.get('topics', []))}")


@app.command()
def stats():
    """Show knowledge base statistics."""
    from github_radar.discover.retrieval import KnowledgeBase
    kb = KnowledgeBase(_get_settings())
    s = kb.stats()
    console.print(f"Repos indexed: {s['repo_count']}")
    console.print(f"Topics tracked: {s['topic_count']}")
    console.print(f"Relations: {s['relation_count']}")
    if s.get("artifact_dirs"):
        console.print(f"Artifact dirs: {s['artifact_dirs']}")


@app.command()
def graph():
    """Show repo relation graph (text)."""
    from github_radar.discover.retrieval import KnowledgeBase
    from github_radar.memory.relations import RelationGraph
    kb = KnowledgeBase(_get_settings())
    rg = RelationGraph(kb.index)
    clusters = rg.find_clusters()
    if not clusters:
        console.print("[dim]No topic clusters found yet.[/dim]")
        return
    for c in clusters:
        console.print(f"\n[bold]{c['topic']}[/bold] ({c['size']} repos)")
        for r in c["repos"]:
            console.print(f"  - {r}")


@app.command()
def version():
    """Show version."""
    from github_radar import __version__
    console.print(f"github-radar v{__version__}")


def main():
    app()
