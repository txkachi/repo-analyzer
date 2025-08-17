# Repository Analyzer

A comprehensive Python tool for analyzing Git repositories and generating detailed statistics and reports. Supports both local repositories and GitHub repositories with an optional web interface.

## Features

- **Repository Analysis**: File count, size, lines of code, comments, and blank lines
- **Language Detection**: Automatic programming language detection with statistics
- **Git Analysis**: Commit history, contributors, most changed files
- **GitHub Integration**: Fetch metadata from GitHub repositories (stars, forks, issues, PRs)
- **Multiple Output Formats**: JSON, Markdown, and HTML reports with charts
- **Web Interface**: Optional FastAPI-based web dashboard
- **CLI Tool**: Command-line interface with rich output
- **Cross-platform**: Works on Windows, macOS, and Linux

## Quick Start

### Installation

```bash
git clone https://github.com/txkachi/repo-analyzer.git
cd repo-analyzer
pip install -e .
```

### Basic Usage

```bash
# Analyze a local repository
repoanalyze analyze /path/to/your/repo

# Analyze a GitHub repository
repoanalyze analyze https://github.com/username/repository

# Generate reports
repoanalyze analyze /path/to/repo --json --md --html

# Show top 10 most changed files
repoanalyze analyze /path/to/repo --top 10

# Use GitHub token for enhanced metadata
repoanalyze analyze https://github.com/username/repo --token YOUR_GITHUB_TOKEN
```

## Requirements

- Python 3.11+
- Git installed and accessible
- Optional: GitHub personal access token for enhanced metadata

## Installation Options

### Development Dependencies

```bash
pip install 'repo-analyzer[dev]'
```

This installs additional tools for development:
- pytest (testing)
- black (code formatting)
- isort (import sorting)
- mypy (type checking)
- flake8 (linting)

### Web Interface Dependencies

```bash
pip install 'repo-analyzer[web]'
```

## Usage Examples

### Command Line Interface

#### Basic Analysis
```bash
# Analyze local repository
repoanalyze analyze /home/user/projects/my-project

# Analyze GitHub repository
repoanalyze analyze https://github.com/username/awesome-project
```

#### Generate Reports
```bash
# Generate all report formats
repoanalyze analyze /path/to/repo --json --md --html

# Custom output directory
repoanalyze analyze /path/to/repo --json --md --html --output-dir ./reports

# Custom filenames
repoanalyze analyze /path/to/repo --json my_report.json --md README_analysis.md
```

#### Advanced Options
```bash
# Show top 20 most changed files
repoanalyze analyze /path/to/repo --top 20

# Use GitHub token from environment variable
export GITHUB_TOKEN=your_token_here
repoanalyze analyze https://github.com/username/repo

# Verbose logging
repoanalyze analyze /path/to/repo --verbose

# Help
repoanalyze --help
```

### Web Interface

Start the web server:
```bash
repoanalyze web

# Custom host and port
repoanalyze web --host 0.0.0.0 --port 8080

# Enable auto-reload for development
repoanalyze web --reload
```

Then open your browser to `http://localhost:8000` and use the web interface to analyze repositories.

## Report Formats

### JSON Report
Machine-readable format with all analysis data:
```json
{
  "repository_path": "/path/to/repo",
  "analysis_date": "2024-01-15T10:30:00",
  "total_files": 150,
  "total_size_mb": 2.5,
  "total_lines_of_code": 5000,
  "languages": [...],
  "git_stats": {...}
}
```

### Markdown Report
Perfect for adding to GitHub READMEs:
```markdown
# Repository Analysis Report

**Repository:** /path/to/repo  
**Analysis Date:** 2024-01-15 10:30:00

## Repository Overview
- **Total Files:** 150
- **Repository Size:** 2.5 MB
- **Total Lines of Code:** 5,000
```

### HTML Report
Interactive report with charts and visualizations:
- Repository overview cards
- Language distribution pie charts
- File count bar charts
- Commit activity timeline
- Responsive design for all devices

## Project Structure

```
repo-analyzer/
├── src/repo_analyzer/
│   ├── __init__.py          # Package initialization
│   ├── analyzer.py          # Core analysis logic
│   ├── models.py            # Data models (Pydantic)
│   ├── utils.py             # Utility functions
│   ├── github_client.py     # GitHub API client
│   ├── reporters.py         # Report generation
│   ├── cli.py              # Command-line interface
│   ├── web_app.py          # FastAPI web application
│   └── templates/          # HTML templates
│       ├── index.html      # Main page
│       ├── result.html     # Results page
│       └── error.html      # Error page
├── tests/                  # Unit tests
├── examples/               # Sample reports
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Testing

Run the test suite:
```bash
# Install development dependencies
pip install 'repo-analyzer[dev]'

# Run tests
pytest

# Run with coverage
pytest --cov=repo_analyzer --cov-report=html

# Run specific test file
pytest tests/test_analyzer.py
```

## Development

### Code Quality Tools

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

### Building and Distribution

```bash
# Build package
python -m build

# Install in development mode
pip install -e .
```

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token for API access

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` scope
3. Use the token with the `--token` option or set `GITHUB_TOKEN` environment variable

## Examples

### Sample Repository Analysis

```bash
# Clone a sample repository
git clone https://github.com/username/sample-project.git

# Analyze it
repoanalyze analyze sample-project --json --md --html --top 10

# View the results
open analysis.html  # HTML report
cat analysis.md     # Markdown report
cat analysis.json   # JSON data
```

### Integration with CI/CD

```yaml
# GitHub Actions example
- name: Analyze Repository
  run: |
    pip install repo-analyzer
    repoanalyze analyze . --json --md --html --output-dir ./analysis
    repoanalyze analyze . --top 20 > top_files.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/txkachi/repo-analyzer.git
cd repo-analyzer
pip install -e '.[dev]'
pre-commit install
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [GitPython](https://github.com/gitpython-developers/GitPython) for Git repository access
- [Pygments](https://pygments.org/) for syntax highlighting and language detection
- [FastAPI](https://fastapi.tiangolo.com/) for the web interface
- [Plotly](https://plotly.com/) for interactive charts
- [Rich](https://rich.readthedocs.io/) for beautiful CLI output

## Support

- **Issues**: [GitHub Issues](https://github.com/txkachi/repo-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/txkachi/repo-analyzer/discussions)
- **Documentation**: [GitHub Wiki](https://github.com/txkachi/repo-analyzer/wiki)
