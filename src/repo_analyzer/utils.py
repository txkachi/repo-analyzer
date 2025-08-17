"""Utility functions for the Repo Analyzer."""

import re
from pathlib import Path
from typing import Tuple


def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is binary, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        return True


def count_lines(file_path: Path, language: str) -> Tuple[int, int, int]:
    """Count lines of code, comments, and blank lines in a file.
    
    Args:
        file_path: Path to the file to analyze
        language: Programming language of the file
        
    Returns:
        Tuple of (lines_of_code, lines_of_comments, blank_lines)
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return 0, 0, 0
    
    lines_of_code = 0
    lines_of_comments = 0
    blank_lines = 0
    
    # Language-specific comment patterns
    comment_patterns = {
        'Python': (r'^\s*#', r'^\s*"""', r'^\s*"""'),
        'JavaScript': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'TypeScript': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'Java': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'C++': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'C': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'C#': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'PHP': (r'^\s*//', r'^\s*#', r'^\s*/\*', r'\*/'),
        'Ruby': (r'^\s*#', r'^\s*=begin', r'=end'),
        'Go': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'Rust': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'Swift': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'Kotlin': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'Scala': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'HTML': (r'^\s*<!--', r'-->'),
        'CSS': (r'^\s*/\*', r'\*/'),
        'SCSS': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'Sass': (r'^\s*//', r'^\s*/\*', r'\*/'),
        'SQL': (r'^\s*--', r'^\s*/\*', r'\*/'),
        'Shell': (r'^\s*#'),
        'Batch': (r'^\s*::', r'^\s*REM'),
        'PowerShell': (r'^\s*#', r'^\s*<#', r'#>'),
    }
    
    # Get comment patterns for the language
    patterns = comment_patterns.get(language, ())
    
    in_multiline_comment = False
    multiline_start = None
    multiline_end = None
    
    # Set up multiline comment patterns
    if language in ['Python', 'Ruby']:
        multiline_start = r'^\s*"""'
        multiline_end = r'^\s*"""'
    elif language in ['JavaScript', 'TypeScript', 'Java', 'C++', 'C', 'C#', 'PHP', 'Go', 'Rust', 'Swift', 'Kotlin', 'Scala', 'CSS', 'SCSS', 'Sass', 'SQL']:
        multiline_start = r'^\s*/\*'
        multiline_end = r'\*/'
    
    for line in lines:
        line = line.rstrip('\r\n')
        
        # Skip empty lines
        if not line.strip():
            blank_lines += 1
            continue
        
        # Check for multiline comment start
        if multiline_start and re.search(multiline_start, line):
            in_multiline_comment = True
            lines_of_comments += 1
            continue
        
        # Check for multiline comment end
        if multiline_end and re.search(multiline_end, line):
            in_multiline_comment = False
            lines_of_comments += 1
            continue
        
        # If we're in a multiline comment, count as comment
        if in_multiline_comment:
            lines_of_comments += 1
            continue
        
        # Check for single-line comments
        is_comment = False
        for pattern in patterns:
            if re.search(pattern, line):
                lines_of_comments += 1
                is_comment = True
                break
        
        if not is_comment:
            lines_of_code += 1
    
    return lines_of_code, lines_of_comments, blank_lines


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"
    
    return filename
