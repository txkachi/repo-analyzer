"""Unit tests for the utils module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from repo_analyzer.utils import is_binary_file, count_lines, format_file_size, sanitize_filename


class TestUtils:
    """Test cases for utility functions."""
    
    def test_is_binary_file_binary(self):
        """Test binary file detection."""
        # Mock binary content with null bytes
        mock_content = b'Hello\x00World'
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            result = is_binary_file(Path('test.bin'))
            assert result is True
    
    def test_is_binary_file_text(self):
        """Test text file detection."""
        # Mock text content without null bytes
        mock_content = b'Hello World\nThis is text'
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            result = is_binary_file(Path('test.txt'))
            assert result is False
    
    def test_is_binary_file_exception(self):
        """Test binary file detection with exception."""
        with patch('builtins.open', side_effect=Exception("File error")):
            result = is_binary_file(Path('test.txt'))
            assert result is True  # Should return True on error
    
    def test_count_lines_python(self):
        """Test line counting for Python files."""
        mock_content = '''# This is a comment
def hello():
    """Docstring comment"""
    print("Hello")  # Inline comment
    
    return True
'''
        
        with patch('builtins.open', mock_open(read_data=mock_content.encode())):
            result = count_lines(Path('test.py'), 'Python')
            
            assert result[0] == 3  # Lines of code
            assert result[1] == 3  # Lines of comments
            assert result[2] == 2  # Blank lines
    
    def test_count_lines_javascript(self):
        """Test line counting for JavaScript files."""
        mock_content = '''// Single line comment
function hello() {
    /* Multi-line
       comment */
    console.log("Hello"); // Inline comment
    
    return true;
}
'''
        
        with patch('builtins.open', mock_open(read_data=mock_content.encode())):
            result = count_lines(Path('test.js'), 'JavaScript')
            
            assert result[0] == 3  # Lines of code
            assert result[1] == 4  # Lines of comments
            assert result[2] == 2  # Blank lines
    
    def test_count_lines_html(self):
        """Test line counting for HTML files."""
        mock_content = '''<!DOCTYPE html>
<html>
    <!-- HTML comment -->
    <head>
        <title>Test</title>
    </head>
    <body>
        <h1>Hello</h1>
    </body>
</html>
'''
        
        with patch('builtins.open', mock_open(read_data=mock_content.encode())):
            result = count_lines(Path('test.html'), 'HTML')
            
            assert result[0] == 8  # Lines of code
            assert result[1] == 1  # Lines of comments
            assert result[2] == 2  # Blank lines
    
    def test_count_lines_binary(self):
        """Test line counting for binary files."""
        result = count_lines(Path('test.bin'), 'Binary')
        
        assert result[0] == 0  # Lines of code
        assert result[1] == 0  # Lines of comments
        assert result[2] == 0  # Blank lines
    
    def test_count_lines_exception(self):
        """Test line counting with file read exception."""
        with patch('builtins.open', side_effect=Exception("File error")):
            result = count_lines(Path('test.txt'), 'Text')
            
            assert result[0] == 0  # Lines of code
            assert result[1] == 0  # Lines of comments
            assert result[2] == 0  # Blank lines
    
    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        assert format_file_size(500) == "500 B"
        assert format_file_size(1023) == "1023 B"
    
    def test_format_file_size_kilobytes(self):
        """Test file size formatting for kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(2048) == "2.0 KB"
        assert format_file_size(1536) == "1.5 KB"
    
    def test_format_file_size_megabytes(self):
        """Test file size formatting for megabytes."""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(2 * 1024 * 1024) == "2.0 MB"
        assert format_file_size(1.5 * 1024 * 1024) == "1.5 MB"
    
    def test_format_file_size_gigabytes(self):
        """Test file size formatting for gigabytes."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(2 * 1024 * 1024 * 1024) == "2.0 GB"
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test invalid characters
        assert sanitize_filename('file<name>') == 'file_name_'
        assert sanitize_filename('file:name') == 'file_name'
        assert sanitize_filename('file/name') == 'file_name'
        assert sanitize_filename('file\\name') == 'file_name'
        assert sanitize_filename('file|name') == 'file_name'
        assert sanitize_filename('file?name') == 'file_name'
        assert sanitize_filename('file*name') == 'file_name'
        
        # Test leading/trailing spaces and dots
        assert sanitize_filename('  filename  ') == 'filename'
        assert sanitize_filename('...filename...') == 'filename'
        
        # Test empty filename
        assert sanitize_filename('') == 'unnamed'
        assert sanitize_filename('   ') == 'unnamed'
        assert sanitize_filename('...') == 'unnamed'
    
    def test_sanitize_filename_safe(self):
        """Test that safe filenames are not changed."""
        safe_names = [
            'filename.txt',
            'my_file_123.py',
            'README.md',
            'package.json',
            'file-name_with.extension'
        ]
        
        for name in safe_names:
            assert sanitize_filename(name) == name


if __name__ == '__main__':
    pytest.main([__file__])
