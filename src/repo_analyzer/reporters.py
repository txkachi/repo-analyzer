"""Report generation modules for different output formats."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from .models import AnalysisResult, FileInfo
from .utils import format_file_size

logger = logging.getLogger(__name__)


class BaseReporter:
    """Base class for all reporters."""
    
    def __init__(self, result: AnalysisResult):
        """Initialize the reporter.
        
        Args:
            result: Analysis result to report on
        """
        self.result = result
    
    def generate(self, output_path: Optional[str] = None) -> str:
        """Generate the report.
        
        Args:
            output_path: Optional path to save the report
            
        Returns:
            Generated report content
        """
        raise NotImplementedError


class JSONReporter(BaseReporter):
    """Generate JSON reports."""
    
    def generate(self, output_path: Optional[str] = None) -> str:
        """Generate a JSON report.
        
        Args:
            output_path: Optional path to save the report
            
        Returns:
            JSON report content
        """
        # Convert datetime objects to ISO format for JSON serialization
        report_data = self.result.model_dump()
        report_data["analysis_date"] = report_data["analysis_date"].isoformat()
        
        if self.result.github_metadata:
            github_data = report_data["github_metadata"]
            if github_data.get("created_at"):
                github_data["created_at"] = github_data["created_at"].isoformat()
            if github_data.get("updated_at"):
                github_data["updated_at"] = github_data["updated_at"].isoformat()
        
        json_content = json.dumps(report_data, indent=2, ensure_ascii=False)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_content)
            logger.info(f"JSON report saved to: {output_path}")
        
        return json_content


class MarkdownReporter(BaseReporter):
    """Generate Markdown reports."""
    
    def generate(self, output_path: Optional[str] = None) -> str:
        """Generate a Markdown report.
        
        Args:
            output_path: Optional path to save the report
            
        Returns:
            Markdown report content
        """
        md_content = []
        
        # Header
        md_content.append(f"# Repository Analysis Report")
        md_content.append(f"")
        md_content.append(f"**Repository:** {self.result.repository_path}")
        md_content.append(f"**Analysis Date:** {self.result.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append(f"")
        
        # Repository Overview
        md_content.append(f"## Repository Overview")
        md_content.append(f"")
        md_content.append(f"- **Total Files:** {self.result.total_files:,}")
        md_content.append(f"- **Repository Size:** {self.result.total_size_mb:.2f} MB")
        md_content.append(f"- **Total Lines of Code:** {self.result.total_lines_of_code:,}")
        md_content.append(f"- **Total Lines of Comments:** {self.result.total_lines_of_comments:,}")
        md_content.append(f"- **Total Blank Lines:** {self.result.total_blank_lines:,}")
        md_content.append(f"")
        
        # Language Statistics
        md_content.append(f"## Language Statistics")
        md_content.append(f"")
        md_content.append(f"| Language | Files | Lines | Percentage |")
        md_content.append(f"|----------|-------|-------|------------|")
        
        for lang in self.result.languages:
            md_content.append(
                f"| {lang.language} | {lang.file_count:,} | {lang.total_lines:,} | {lang.percentage:.1f}% |"
            )
        md_content.append(f"")
        
        # Git Statistics
        md_content.append(f"## Git Statistics")
        md_content.append(f"")
        md_content.append(f"- **Total Commits:** {self.result.git_stats.total_commits:,}")
        md_content.append(f"- **Contributors:** {len(self.result.git_stats.contributors)}")
        md_content.append(f"")
        
        if self.result.git_stats.top_contributors:
            md_content.append(f"### Top Contributors")
            md_content.append(f"")
            for author, count in list(self.result.git_stats.top_contributors.items())[:5]:
                md_content.append(f"- **{author}:** {count:,} commits")
            md_content.append(f"")
        
        if self.result.git_stats.most_changed_files:
            md_content.append(f"### Most Changed Files")
            md_content.append(f"")
            for file_path in self.result.git_stats.most_changed_files[:5]:
                md_content.append(f"- `{file_path}`")
            md_content.append(f"")
        
        # File Analysis
        md_content.append(f"## File Analysis")
        md_content.append(f"")
        
        md_content.append(f"### Largest Files (by size)")
        md_content.append(f"")
        for file_info in self.result.largest_files[:5]:
            md_content.append(f"- `{file_info.path}` - {format_file_size(file_info.size_bytes)}")
        md_content.append(f"")
        
        md_content.append(f"### Files with Most Lines of Code")
        md_content.append(f"")
        for file_info in self.result.files_by_lines[:5]:
            md_content.append(f"- `{file_info.path}` - {file_info.lines_of_code:,} lines")
        md_content.append(f"")
        
        # Directory Structure
        md_content.append(f"## Directory Structure")
        md_content.append(f"")
        for directory, count in list(self.result.directory_structure.items())[:10]:
            md_content.append(f"- `{directory}/` - {count:,} files")
        md_content.append(f"")
        
        # GitHub Metadata (if available)
        if self.result.github_metadata:
            md_content.append(f"## GitHub Metadata")
            md_content.append(f"")
            github = self.result.github_metadata
            md_content.append(f"- **Stars:** {github.stars:,}")
            md_content.append(f"- **Forks:** {github.forks:,}")
            md_content.append(f"- **Watchers:** {github.watchers:,}")
            md_content.append(f"- **Open Issues:** {github.open_issues:,}")
            md_content.append(f"- **Open Pull Requests:** {github.open_pull_requests:,}")
            if github.description:
                md_content.append(f"- **Description:** {github.description}")
            md_content.append(f"")
        
        markdown_content = "\n".join(md_content)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logger.info(f"Markdown report saved to: {output_path}")
        
        return markdown_content


class HTMLReporter(BaseReporter):
    """Generate HTML reports with charts."""
    
    def __init__(self, result: AnalysisResult):
        """Initialize the HTML reporter.
        
        Args:
            result: Analysis result to report on
        """
        super().__init__(result)
        self._setup_plotly()
    
    def _setup_plotly(self):
        """Set up Plotly configuration."""
        import plotly.io as pio
        pio.templates.default = "plotly_white"
    
    def generate(self, output_path: Optional[str] = None) -> str:
        """Generate an HTML report with charts.
        
        Args:
            output_path: Optional path to save the report
            
        Returns:
            HTML report content
        """
        html_content = []
        
        # HTML header
        html_content.append(self._get_html_header())
        
        # Repository overview section
        html_content.append(self._generate_overview_section())
        
        # Language charts
        html_content.append(self._generate_language_charts())
        
        # Git statistics
        html_content.append(self._generate_git_section())
        
        # File analysis
        html_content.append(self._generate_file_analysis_section())
        
        # Directory structure
        html_content.append(self._generate_directory_section())
        
        # GitHub metadata (if available)
        if self.result.github_metadata:
            html_content.append(self._generate_github_section())
        
        # HTML footer
        html_content.append(self._get_html_footer())
        
        html_content_str = "\n".join(html_content)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content_str)
            logger.info(f"HTML report saved to: {output_path}")
        
        return html_content_str
    
    def _get_html_header(self) -> str:
        """Generate HTML header with CSS and JavaScript."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Repository Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .file-list {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .file-item {
            padding: 5px 0;
            border-bottom: 1px solid #e9ecef;
        }
        .file-item:last-child {
            border-bottom: none;
        }
        .github-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .github-stat {
            background: #24292e;
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .github-stat-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #58a6ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Repository Analysis Report</h1>
        <p><strong>Repository:</strong> {repo_path}</p>
        <p><strong>Analysis Date:</strong> {analysis_date}</p>
        """.format(
            repo_path=self.result.repository_path,
            analysis_date=self.result.analysis_date.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def _generate_overview_section(self) -> str:
        """Generate the overview section with statistics cards."""
        return f"""
        <h2>📈 Repository Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{self.result.total_files:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.result.total_size_mb:.1f}</div>
                <div class="stat-label">Size (MB)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.result.total_lines_of_code:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.result.total_lines_of_comments:,}</div>
                <div class="stat-label">Comment Lines</div>
            </div>
        </div>
        """
    
    def _generate_language_charts(self) -> str:
        """Generate language distribution charts."""
        # Prepare data for charts
        languages = [lang.language for lang in self.result.languages[:10]]
        lines = [lang.total_lines for lang in self.result.languages[:10]]
        files = [lang.file_count for lang in self.result.languages[:10]]
        
        # Create pie chart for language distribution
        pie_fig = go.Figure(data=[go.Pie(
            labels=languages,
            values=lines,
            hole=0.3,
            textinfo='label+percent',
            textposition='outside'
        )])
        pie_fig.update_layout(
            title="Language Distribution by Lines of Code",
            height=500,
            showlegend=False
        )
        
        # Create bar chart for file counts
        bar_fig = go.Figure(data=[go.Bar(
            x=languages,
            y=files,
            marker_color='#3498db'
        )])
        bar_fig.update_layout(
            title="Files per Language",
            xaxis_title="Language",
            yaxis_title="Number of Files",
            height=400
        )
        
        return f"""
        <h2>🔤 Language Statistics</h2>
        <div class="chart-container">
            <div id="language-pie-chart"></div>
        </div>
        <div class="chart-container">
            <div id="language-bar-chart"></div>
        </div>
        
        <script>
            {pie_fig.to_json()}
            Plotly.newPlot('language-pie-chart', pie_fig.data, pie_fig.layout);
            
            {bar_fig.to_json()}
            Plotly.newPlot('language-bar-chart', bar_fig.data, bar_fig.layout);
        </script>
        """
    
    def _generate_git_section(self) -> str:
        """Generate Git statistics section."""
        # Create commit activity chart
        if self.result.git_stats.commit_activity:
            dates = list(self.result.git_stats.commit_activity.keys())[-30:]  # Last 30 days
            commits = [self.result.git_stats.commit_activity[date] for date in dates]
            
            activity_fig = go.Figure(data=[go.Scatter(
                x=dates,
                y=commits,
                mode='lines+markers',
                line=dict(color='#27ae60', width=3),
                marker=dict(size=6)
            )])
            activity_fig.update_layout(
                title="Commit Activity (Last 30 Days)",
                xaxis_title="Date",
                yaxis_title="Number of Commits",
                height=400
            )
            
            activity_chart = f"""
            <div class="chart-container">
                <div id="commit-activity-chart"></div>
            </div>
            <script>
                {activity_fig.to_json()}
                Plotly.newPlot('commit-activity-chart', activity_fig.data, activity_fig.layout);
            </script>
            """
        else:
            activity_chart = ""
        
        return f"""
        <h2>📝 Git Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{self.result.git_stats.total_commits:,}</div>
                <div class="stat-label">Total Commits</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.result.git_stats.contributors)}</div>
                <div class="stat-label">Contributors</div>
            </div>
        </div>
        
        {activity_chart}
        
        <h3>Top Contributors</h3>
        <div class="file-list">
        """
        + "\n".join([
            f'<div class="file-item"><strong>{author}:</strong> {count:,} commits</div>'
            for author, count in list(self.result.git_stats.top_contributors.items())[:5]
        ]) + """
        </div>
        """
    
    def _generate_file_analysis_section(self) -> str:
        """Generate file analysis section."""
        return f"""
        <h2>📁 File Analysis</h2>
        
        <h3>Largest Files (by size)</h3>
        <div class="file-list">
        """
        + "\n".join([
            f'<div class="file-item"><code>{file_info.path}</code> - {format_file_size(file_info.size_bytes)}</div>'
            for file_info in self.result.largest_files[:5]
        ]) + """
        </div>
        
        <h3>Files with Most Lines of Code</h3>
        <div class="file-list">
        """
        + "\n".join([
            f'<div class="file-item"><code>{file_info.path}</code> - {file_info.lines_of_code:,} lines</div>'
            for file_info in self.result.files_by_lines[:5]
        ]) + """
        </div>
        """
    
    def _generate_directory_section(self) -> str:
        """Generate directory structure section."""
        return f"""
        <h2>📂 Directory Structure</h2>
        <div class="file-list">
        """
        + "\n".join([
            f'<div class="file-item"><code>{directory}/</code> - {count:,} files</div>'
            for directory, count in list(self.result.directory_structure.items())[:10]
        ]) + """
        </div>
        """
    
    def _generate_github_section(self) -> str:
        """Generate GitHub metadata section."""
        github = self.result.github_metadata
        return f"""
        <h2>🐙 GitHub Metadata</h2>
        <div class="github-stats">
            <div class="github-stat">
                <div class="github-stat-number">⭐ {github.stars:,}</div>
                <div>Stars</div>
            </div>
            <div class="github-stat">
                <div class="github-stat-number">🍴 {github.forks:,}</div>
                <div>Forks</div>
            </div>
            <div class="github-stat">
                <div class="github-stat-number">👀 {github.watchers:,}</div>
                <div>Watchers</div>
            </div>
            <div class="github-stat">
                <div class="github-stat-number">🐛 {github.open_issues:,}</div>
                <div>Open Issues</div>
            </div>
            <div class="github-stat">
                <div class="github-stat-number">🔀 {github.open_pull_requests:,}</div>
                <div>Open PRs</div>
            </div>
        </div>
        """
    
    def _get_html_footer(self) -> str:
        """Generate HTML footer."""
        return """
    </div>
</body>
</html>
        """
