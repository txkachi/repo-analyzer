"""Command-line interface for the Repository Analyzer."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from .analyzer import RepoAnalyzer
from .reporters import JSONReporter, MarkdownReporter, HTMLReporter

# Create Typer app
app = typer.Typer(
    name="repoanalyze",
    help="Analyze Git repositories and generate detailed reports",
    add_completion=False,
)

# Rich console for better output
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@app.command()
def analyze(
    repo_path: str = typer.Argument(
        ...,
        help="Path to local repository or GitHub repository URL"
    ),
    json_output: Optional[str] = typer.Option(
        None,
        "--json",
        "-j",
        help="Export analysis as JSON file"
    ),
    markdown_output: Optional[str] = typer.Option(
        None,
        "--md",
        "-m",
        help="Export analysis as Markdown file"
    ),
    html_output: Optional[str] = typer.Option(
        None,
        "--html",
        "-H",
        help="Export analysis as HTML report with charts"
    ),
    top_files: Optional[int] = typer.Option(
        None,
        "--top",
        "-t",
        help="Show top N most frequently changed files"
    ),
    github_token: Optional[str] = typer.Option(
        None,
        "--token",
        envvar="GITHUB_TOKEN",
        help="GitHub personal access token for API access"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging"
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for reports (default: current directory)"
    ),
):
    """Analyze a Git repository and generate reports.
    
    Examples:
        # Analyze local repository
        repoanalyze analyze /path/to/repo
        
        # Analyze GitHub repository
        repoanalyze analyze https://github.com/username/repo
        
        # Generate all report formats
        repoanalyze analyze /path/to/repo --json --md --html
        
        # Show top 10 most changed files
        repoanalyze analyze /path/to/repo --top 10
        
        # Use GitHub token for enhanced metadata
        repoanalyze analyze https://github.com/username/repo --token YOUR_TOKEN
    """
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate inputs
    if not repo_path:
        console.print("[red]Error: Repository path is required[/red]")
        console.print("Usage: repoanalyze analyze <repository_path> [options]")
        console.print("Use 'repoanalyze --help' for more information")
        sys.exit(1)
    
    # Set output directory
    if output_dir and output_dir is not None:
        output_path = Path(str(output_dir))
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()
    
    # Check if any output format is specified
    has_output = any([json_output, markdown_output, html_output])
    
    try:
        # Show analysis progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing repository...", total=None)
            
            # Initialize analyzer
            analyzer = RepoAnalyzer(repo_path, github_token)
            
            # Perform analysis
            result = analyzer.analyze()
            
            progress.update(task, description="Analysis completed! Generating reports...")
        
        # Display summary
        display_summary(result, top_files)
        
        # Generate reports if requested
        if has_output:
            generate_reports(result, output_path, json_output, markdown_output, html_output)
        
        # Cleanup
        analyzer.cleanup()
        
        console.print("\n[green]Analysis completed successfully.[/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error during analysis: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def display_summary(result, top_files: Optional[int] = None):
    """Display a summary of the analysis results."""
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        f"[bold blue]Repository Analysis Summary[/bold blue]\n"
        f"Repository: {result.repository_path}\n"
        f"Analysis Date: {result.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="blue"
    ))
    
    # Repository overview
    overview_table = Table(title="Repository Overview", show_header=True, header_style="bold magenta")
    overview_table.add_column("Metric", style="cyan")
    overview_table.add_column("Value", style="green")
    
    overview_table.add_row("Total Files", f"{result.total_files:,}")
    overview_table.add_row("Repository Size", f"{result.total_size_mb:.2f} MB")
    overview_table.add_row("Lines of Code", f"{result.total_lines_of_code:,}")
    overview_table.add_row("Lines of Comments", f"{result.total_lines_of_comments:,}")
    overview_table.add_row("Blank Lines", f"{result.total_blank_lines:,}")
    
    console.print(overview_table)
    
    # Language statistics
    if result.languages:
        lang_table = Table(title="Top Languages", show_header=True, header_style="bold magenta")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Files", style="green")
        lang_table.add_column("Lines", style="green")
        lang_table.add_column("Percentage", style="yellow")
        
        for lang in result.languages[:5]:
            lang_table.add_row(
                lang.language,
                f"{lang.file_count:,}",
                f"{lang.total_lines:,}",
                f"{lang.percentage:.1f}%"
            )
        
        console.print(lang_table)
    
    # Git statistics
    git_table = Table(title="Git Statistics", show_header=True, header_style="bold magenta")
    git_table.add_column("Metric", style="cyan")
    git_table.add_column("Value", style="green")
    
    git_table.add_row("Total Commits", f"{result.git_stats.total_commits:,}")
    git_table.add_row("Contributors", f"{len(result.git_stats.contributors)}")
    
    if result.git_stats.top_contributors:
        git_table.add_row("Top Contributor", 
                         f"{list(result.git_stats.top_contributors.keys())[0]} "
                         f"({list(result.git_stats.top_contributors.values())[0]:,} commits)")
    
    console.print(git_table)
    
    # Most changed files
    if top_files and result.git_stats.most_changed_files:
        files_table = Table(title=f"Top {top_files} Most Changed Files", show_header=True, header_style="bold magenta")
        files_table.add_column("Rank", style="cyan")
        files_table.add_column("File Path", style="green")
        
        for i, file_path in enumerate(result.git_stats.most_changed_files[:top_files], 1):
            files_table.add_row(str(i), file_path)
        
        console.print(files_table)
    
    # GitHub metadata (if available)
    if result.github_metadata:
        github_table = Table(title="GitHub Metadata", show_header=True, header_style="bold magenta")
        github_table.add_column("Metric", style="cyan")
        github_table.add_column("Value", style="green")
        
        github = result.github_metadata
        github_table.add_row("Stars", f"{github.stars:,}")
        github_table.add_row("Forks", f"{github.forks:,}")
        github_table.add_row("Watchers", f"{github.watchers:,}")
        github_table.add_row("Open Issues", f"{github.open_issues:,}")
        github_table.add_row("Open Pull Requests", f"{github.open_pull_requests:,}")
        
        if github.description:
            github_table.add_row("Description", github.description[:100] + "..." if len(github.description) > 100 else github.description)
        
        console.print(github_table)
    
    console.print("="*80)


def generate_reports(result, output_path: Path, json_output: Optional[str], 
                    markdown_output: Optional[str], html_output: Optional[str]):
    """Generate the requested report formats."""
    console.print("\n[bold blue]Generating Reports...[/bold blue]")
    
    if json_output:
        json_file = output_path / (json_output if json_output != "json" else "analysis.json")
        reporter = JSONReporter(result)
        reporter.generate(str(json_file))
        console.print(f"[green]JSON report saved to: {json_file}[/green]")
    
    if markdown_output:
        md_file = output_path / (markdown_output if markdown_output != "md" else "analysis.md")
        reporter = MarkdownReporter(result)
        reporter.generate(str(md_file))
        console.print(f"[green]Markdown report saved to: {md_file}[/green]")
    
    if html_output:
        html_file = output_path / (html_output if html_output != "html" else "analysis.html")
        reporter = HTMLReporter(result)
        reporter.generate(str(html_file))
        console.print(f"[green]HTML report saved to: {html_file}[/green]")


@app.command()
def version():
    """Show version information."""
    from . import __version__
    console.print(f"[bold blue]Repository Analyzer v{__version__}[/bold blue]")


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Start the web interface."""
    try:
        import uvicorn
        from .web_app import app as web_app
        
        console.print(f"[bold blue]Starting web interface...[/bold blue]")
        console.print(f"[green]Web interface will be available at: http://{host}:{port}[/green]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        
        uvicorn.run(
            web_app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except ImportError:
        console.print("[red]Error: Web interface dependencies not installed. Install with: pip install 'repo-analyzer[web]'[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error starting web interface: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()
