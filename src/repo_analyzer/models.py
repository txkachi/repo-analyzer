"""Data models for the Repo Analyzer."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Information about a single file."""
    
    path: str = Field(..., description="File path relative to repository root")
    size_bytes: int = Field(..., description="File size in bytes")
    lines_of_code: int = Field(..., description="Total lines of code")
    lines_of_comments: int = Field(..., description="Lines of comments")
    blank_lines: int = Field(..., description="Blank lines")
    language: str = Field(..., description="Detected programming language")
    is_binary: bool = Field(..., description="Whether the file is binary")


class LanguageStats(BaseModel):
    """Statistics for a programming language."""
    
    language: str = Field(..., description="Programming language name")
    file_count: int = Field(..., description="Number of files in this language")
    total_lines: int = Field(..., description="Total lines of code")
    percentage: float = Field(..., description="Percentage of total code")


class GitStats(BaseModel):
    """Git repository statistics."""
    
    total_commits: int = Field(..., description="Total number of commits")
    contributors: List[str] = Field(..., description="List of contributor names")
    top_contributors: Dict[str, int] = Field(..., description="Top contributors with commit counts")
    most_changed_files: List[str] = Field(..., description="Most frequently changed files")
    commit_activity: Dict[str, int] = Field(..., description="Commit activity by date")


class GitHubMetadata(BaseModel):
    """GitHub repository metadata."""
    
    stars: int = Field(..., description="Number of stars")
    forks: int = Field(..., description="Number of forks")
    watchers: int = Field(..., description="Number of watchers")
    open_issues: int = Field(..., description="Number of open issues")
    open_pull_requests: int = Field(..., description="Number of open pull requests")
    description: Optional[str] = Field(None, description="Repository description")
    language: Optional[str] = Field(None, description="Primary language")
    created_at: Optional[datetime] = Field(None, description="Repository creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")


class AnalysisResult(BaseModel):
    """Complete analysis result for a repository."""
    
    repository_path: str = Field(..., description="Path or URL to the repository")
    analysis_date: datetime = Field(..., description="When the analysis was performed")
    
    # Repository information
    total_files: int = Field(..., description="Total number of files")
    total_size_mb: float = Field(..., description="Total repository size in MB")
    total_lines_of_code: int = Field(..., description="Total lines of code")
    total_lines_of_comments: int = Field(..., description="Total lines of comments")
    total_blank_lines: int = Field(..., description="Total blank lines")
    
    # Language breakdown
    languages: List[LanguageStats] = Field(..., description="Language statistics")
    
    # Git analysis
    git_stats: GitStats = Field(..., description="Git repository statistics")
    
    # File analysis
    largest_files: List[FileInfo] = Field(..., description="Largest files by size")
    smallest_files: List[FileInfo] = Field(..., description="Smallest files by size")
    files_by_lines: List[FileInfo] = Field(..., description="Files sorted by lines of code")
    
    # GitHub metadata (if applicable)
    github_metadata: Optional[GitHubMetadata] = Field(None, description="GitHub repository metadata")
    
    # Directory structure
    directory_structure: Dict[str, int] = Field(..., description="Directory structure summary")
