"""Core repository analysis functionality."""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

import git
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.util import ClassNotFound

from .models import (
    AnalysisResult,
    FileInfo,
    LanguageStats,
    GitStats,
    GitHubMetadata,
)
from .github_client import GitHubClient
from .utils import is_binary_file, count_lines

logger = logging.getLogger(__name__)


class RepoAnalyzer:
    """Main repository analyzer class."""
    
    def __init__(self, repo_path: str, github_token: Optional[str] = None):
        """Initialize the analyzer.
        
        Args:
            repo_path: Path to local repository or GitHub URL
            github_token: Optional GitHub token for API access
        """
        self.repo_path = repo_path
        self.github_token = github_token
        self.github_client = GitHubClient(github_token) if github_token else None
        self.is_github_repo = self._is_github_url(repo_path)
        
        if not self.is_github_repo:
            self.repo_path = os.path.abspath(repo_path)
            if not os.path.exists(self.repo_path):
                raise ValueError(f"Repository path does not exist: {self.repo_path}")
        
        self._repo: Optional[git.Repo] = None
        self._analysis_result: Optional[AnalysisResult] = None
    
    def _is_github_url(self, path: str) -> bool:
        """Check if the path is a GitHub URL."""
        return path.startswith(("https://github.com/", "git@github.com:"))
    
    def _get_repo(self) -> git.Repo:
        """Get the Git repository object."""
        if self._repo is None:
            if self.is_github_repo:
                # Clone the repository to a temporary location
                temp_dir = Path.cwd() / f"temp_repo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                temp_dir.mkdir(exist_ok=True)
                logger.info(f"Cloning repository to {temp_dir}")
                self._repo = git.Repo.clone_from(self.repo_path, temp_dir)
            else:
                self._repo = git.Repo(self.repo_path)
        return self._repo
    
    def analyze(self) -> AnalysisResult:
        """Perform complete repository analysis.
        
        Returns:
            AnalysisResult containing all analysis data
        """
        logger.info(f"Starting analysis of repository: {self.repo_path}")
        
        repo = self._get_repo()
        
        # Analyze files
        files_info = self._analyze_files(repo)
        
        # Analyze Git statistics
        git_stats = self._analyze_git_stats(repo)
        
        # Get GitHub metadata if applicable
        github_metadata = None
        if self.is_github_repo and self.github_client:
            github_metadata = self._get_github_metadata()
        
        # Calculate totals and statistics
        total_files = len(files_info)
        total_size_mb = sum(f.size_bytes for f in files_info) / (1024 * 1024)
        total_lines_of_code = sum(f.lines_of_code for f in files_info)
        total_lines_of_comments = sum(f.lines_of_comments for f in files_info)
        total_blank_lines = sum(f.blank_lines for f in files_info)
        
        # Language statistics
        languages = self._calculate_language_stats(files_info, total_lines_of_code)
        
        # File analysis
        largest_files = sorted(files_info, key=lambda x: x.size_bytes, reverse=True)[:10]
        smallest_files = sorted(files_info, key=lambda x: x.size_bytes)[:10]
        files_by_lines = sorted(files_info, key=lambda x: x.lines_of_code, reverse=True)[:10]
        
        # Directory structure
        directory_structure = self._analyze_directory_structure(files_info)
        
        self._analysis_result = AnalysisResult(
            repository_path=self.repo_path,
            analysis_date=datetime.now(),
            total_files=total_files,
            total_size_mb=total_size_mb,
            total_lines_of_code=total_lines_of_code,
            total_lines_of_comments=total_lines_of_comments,
            total_blank_lines=total_blank_lines,
            languages=languages,
            git_stats=git_stats,
            largest_files=largest_files,
            smallest_files=smallest_files,
            files_by_lines=files_by_lines,
            github_metadata=github_metadata,
            directory_structure=directory_structure,
        )
        
        logger.info("Analysis completed successfully")
        return self._analysis_result
    
    def _analyze_files(self, repo: git.Repo) -> List[FileInfo]:
        """Analyze all files in the repository."""
        files_info = []
        repo_path = Path(repo.working_dir)
        
        for file_path in repo_path.rglob("*"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                try:
                    file_info = self._analyze_single_file(file_path, repo_path)
                    if file_info:
                        files_info.append(file_info)
                except Exception as e:
                    logger.warning(f"Error analyzing file {file_path}: {e}")
        
        return files_info
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during analysis."""
        skip_patterns = {
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            ".pytest_cache", ".coverage", "*.pyc", "*.pyo", "*.pyd",
            "*.so", "*.dll", "*.exe", "*.bin", "*.obj", "*.o"
        }
        
        for pattern in skip_patterns:
            if pattern in str(file_path) or file_path.name.endswith(tuple(skip_patterns)):
                return True
        
        return False
    
    def _analyze_single_file(self, file_path: Path, repo_path: Path) -> Optional[FileInfo]:
        """Analyze a single file."""
        try:
            # Get file size
            size_bytes = file_path.stat().st_size
            
            # Check if binary
            is_binary = is_binary_file(file_path)
            
            # Detect language
            language = self._detect_language(file_path)
            
            # Count lines
            if is_binary:
                lines_of_code = lines_of_comments = blank_lines = 0
            else:
                lines_of_code, lines_of_comments, blank_lines = count_lines(file_path, language)
            
            return FileInfo(
                path=str(file_path.relative_to(repo_path)),
                size_bytes=size_bytes,
                lines_of_code=lines_of_code,
                lines_of_comments=lines_of_comments,
                blank_lines=blank_lines,
                language=language,
                is_binary=is_binary,
            )
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect the programming language of a file."""
        try:
            lexer = get_lexer_for_filename(str(file_path))
            return lexer.name
        except ClassNotFound:
            # Try to detect by extension
            extension = file_path.suffix.lower()
            extension_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".ts": "TypeScript",
                ".java": "Java",
                ".cpp": "C++",
                ".c": "C",
                ".h": "C/C++ Header",
                ".cs": "C#",
                ".php": "PHP",
                ".rb": "Ruby",
                ".go": "Go",
                ".rs": "Rust",
                ".swift": "Swift",
                ".kt": "Kotlin",
                ".scala": "Scala",
                ".html": "HTML",
                ".css": "CSS",
                ".scss": "SCSS",
                ".sass": "Sass",
                ".sql": "SQL",
                ".md": "Markdown",
                ".txt": "Text",
                ".json": "JSON",
                ".xml": "XML",
                ".yaml": "YAML",
                ".yml": "YAML",
                ".toml": "TOML",
                ".ini": "INI",
                ".cfg": "Configuration",
                ".conf": "Configuration",
                ".sh": "Shell",
                ".bat": "Batch",
                ".ps1": "PowerShell",
                ".dockerfile": "Dockerfile",
                ".makefile": "Makefile",
            }
            return extension_map.get(extension, "Unknown")
    
    def _analyze_git_stats(self, repo: git.Repo) -> GitStats:
        """Analyze Git repository statistics."""
        try:
            # Get all commits
            commits = list(repo.iter_commits())
            total_commits = len(commits)
            
            # Get contributors
            contributors = set()
            author_counts = Counter()
            
            for commit in commits:
                author = commit.author.name
                contributors.add(author)
                author_counts[author] += 1
            
            # Top contributors
            top_contributors = dict(author_counts.most_common(10))
            
            # Most changed files
            file_changes = Counter()
            for commit in commits:
                for parent in commit.parents:
                    diff = commit.diff(parent)
                    for change in diff:
                        if change.a_path:
                            file_changes[change.a_path] += 1
                        if change.b_path and change.b_path != change.a_path:
                            file_changes[change.b_path] += 1
            
            most_changed_files = [file for file, _ in file_changes.most_common(10)]
            
            # Commit activity
            commit_activity = defaultdict(int)
            for commit in commits:
                date_str = commit.committed_datetime.strftime("%Y-%m-%d")
                commit_activity[date_str] += 1
            
            return GitStats(
                total_commits=total_commits,
                contributors=list(contributors),
                top_contributors=top_contributors,
                most_changed_files=most_changed_files,
                commit_activity=dict(commit_activity),
            )
        except Exception as e:
            logger.warning(f"Error analyzing Git stats: {e}")
            return GitStats(
                total_commits=0,
                contributors=[],
                top_contributors={},
                most_changed_files=[],
                commit_activity={},
            )
    
    def _get_github_metadata(self) -> Optional[GitHubMetadata]:
        """Get GitHub repository metadata."""
        if not self.github_client:
            return None
        
        try:
            # Extract owner and repo from GitHub URL
            if self.repo_path.startswith("https://github.com/"):
                parts = self.repo_path.replace("https://github.com/", "").split("/")
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1].replace(".git", "")
                    return self.github_client.get_repo_metadata(owner, repo)
        except Exception as e:
            logger.warning(f"Error getting GitHub metadata: {e}")
        
        return None
    
    def _calculate_language_stats(
        self, files_info: List[FileInfo], total_lines: int
    ) -> List[LanguageStats]:
        """Calculate language statistics."""
        language_data = defaultdict(lambda: {"files": 0, "lines": 0})
        
        for file_info in files_info:
            language_data[file_info.language]["files"] += 1
            language_data[file_info.language]["lines"] += file_info.lines_of_code
        
        languages = []
        for language, data in language_data.items():
            percentage = (data["lines"] / total_lines * 100) if total_lines > 0 else 0
            languages.append(
                LanguageStats(
                    language=language,
                    file_count=data["files"],
                    total_lines=data["lines"],
                    percentage=round(percentage, 2),
                )
            )
        
        # Sort by lines of code
        return sorted(languages, key=lambda x: x.total_lines, reverse=True)
    
    def _analyze_directory_structure(self, files_info: List[FileInfo]) -> Dict[str, int]:
        """Analyze directory structure."""
        directory_counts = defaultdict(int)
        
        for file_info in files_info:
            path_parts = Path(file_info.path).parts
            for i in range(1, len(path_parts)):
                directory = "/".join(path_parts[:i])
                directory_counts[directory] += 1
        
        return dict(sorted(directory_counts.items(), key=lambda x: x[1], reverse=True))
    
    def get_analysis_result(self) -> Optional[AnalysisResult]:
        """Get the cached analysis result."""
        return self._analysis_result
    
    def cleanup(self):
        """Clean up temporary resources."""
        if self._repo and self.is_github_repo:
            try:
                import shutil
                repo_path = Path(self._repo.working_dir)
                if repo_path.exists():
                    shutil.rmtree(repo_path)
                    logger.info(f"Cleaned up temporary repository: {repo_path}")
            except Exception as e:
                logger.warning(f"Error cleaning up temporary repository: {e}")
