"""Repo Analyzer - A comprehensive tool to analyze Git repositories and generate detailed reports."""

__version__ = "1.0.0"
__author__ = "Repo Analyzer Team"
__email__ = "team@repoanalyzer.com"

from .analyzer import RepoAnalyzer
from .models import AnalysisResult, FileInfo, LanguageStats, GitStats

__all__ = [
    "RepoAnalyzer",
    "AnalysisResult", 
    "FileInfo",
    "LanguageStats",
    "GitStats",
]
