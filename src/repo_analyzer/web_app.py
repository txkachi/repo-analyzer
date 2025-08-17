"""Web interface for the Repository Analyzer using FastAPI."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from .analyzer import RepoAnalyzer
from .reporters import JSONReporter, MarkdownReporter, HTMLReporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Repository Analyzer",
    description="A comprehensive tool for analyzing Git repositories and generating detailed reports",
    version="1.0.0",
)

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with repository input form."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze_repository(
    request: Request,
    repo_path: str = Form(...),
    github_token: Optional[str] = Form(None),
    output_format: str = Form("html")
):
    """Analyze a repository and return results."""
    try:
        # Validate input
        if not repo_path.strip():
            raise HTTPException(status_code=400, detail="Repository path is required")
        
        # Initialize analyzer
        analyzer = RepoAnalyzer(repo_path.strip(), github_token)
        
        # Perform analysis
        result = analyzer.analyze()
        
        # Generate report based on requested format
        if output_format == "json":
            reporter = JSONReporter(result)
            content = reporter.generate()
            return templates.TemplateResponse(
                "result.html",
                {
                    "request": request,
                    "result": result,
                    "report_content": content,
                    "format": "JSON"
                }
            )
        elif output_format == "markdown":
            reporter = MarkdownReporter(result)
            content = reporter.generate()
            return templates.TemplateResponse(
                "result.html",
                {
                    "request": request,
                    "result": result,
                    "report_content": content,
                    "format": "Markdown"
                }
            )
        else:  # HTML
            reporter = HTMLReporter(result)
            content = reporter.generate()
            return templates.TemplateResponse(
                "result.html",
                {
                    "request": request,
                    "result": result,
                    "report_content": content,
                    "format": "HTML"
                }
            )
    
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": str(e),
                "repo_path": repo_path
            }
        )
    finally:
        # Cleanup
        if 'analyzer' in locals():
            analyzer.cleanup()


@app.post("/download")
async def download_report(
    repo_path: str = Form(...),
    github_token: Optional[str] = Form(None),
    output_format: str = Form(...)
):
    """Download a report file."""
    try:
        # Initialize analyzer
        analyzer = RepoAnalyzer(repo_path.strip(), github_token)
        
        # Perform analysis
        result = analyzer.analyze()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'.{output_format}',
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            temp_path = temp_file.name
        
        # Generate report
        if output_format == "json":
            reporter = JSONReporter(result)
            filename = "analysis.json"
        elif output_format == "markdown":
            reporter = MarkdownReporter(result)
            filename = "analysis.md"
        else:  # HTML
            reporter = HTMLReporter(result)
            filename = "analysis.html"
        
        reporter.generate(temp_path)
        
        # Return file for download
        return FileResponse(
            temp_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    
    except Exception as e:
        logger.error(f"Error generating download: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if 'analyzer' in locals():
            analyzer.cleanup()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "repo-analyzer"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
