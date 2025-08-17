"""Unit tests for the analyzer module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from repo_analyzer.analyzer import RepoAnalyzer
from repo_analyzer.models import AnalysisResult, FileInfo, LanguageStats, GitStats


class TestRepoAnalyzer:
    """Test cases for the RepoAnalyzer class."""
    
    def test_init_local_repo(self):
        """Test initialization with local repository path."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.abspath', return_value='/test/path'):
                analyzer = RepoAnalyzer('/test/path')
                assert analyzer.repo_path == '/test/path'
                assert analyzer.is_github_repo is False
                assert analyzer.github_client is None
    
    def test_init_github_repo(self):
        """Test initialization with GitHub URL."""
        analyzer = RepoAnalyzer('https://github.com/username/repo')
        assert analyzer.repo_path == 'https://github.com/username/repo'
        assert analyzer.is_github_repo is True
    
    def test_init_github_repo_with_token(self):
        """Test initialization with GitHub URL and token."""
        analyzer = RepoAnalyzer('https://github.com/username/repo', 'test_token')
        assert analyzer.github_token == 'test_token'
        assert analyzer.github_client is not None
    
    def test_init_local_repo_not_exists(self):
        """Test initialization with non-existent local path."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ValueError, match="Repository path does not exist"):
                RepoAnalyzer('/non/existent/path')
    
    def test_is_github_url(self):
        """Test GitHub URL detection."""
        analyzer = RepoAnalyzer('/test/path')
        
        assert analyzer._is_github_url('https://github.com/username/repo') is True
        assert analyzer._is_github_url('git@github.com:username/repo.git') is True
        assert analyzer._is_github_url('/local/path') is False
        assert analyzer._is_github_url('https://gitlab.com/username/repo') is False
    
    @patch('git.Repo')
    def test_get_repo_local(self, mock_git_repo):
        """Test getting local repository."""
        mock_repo = Mock()
        mock_git_repo.return_value = mock_repo
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.abspath', return_value='/test/path'):
                analyzer = RepoAnalyzer('/test/path')
                repo = analyzer._get_repo()
                
                assert repo == mock_repo
                mock_git_repo.assert_called_once_with('/test/path')
    
    @patch('git.Repo.clone_from')
    def test_get_repo_github(self, mock_clone):
        """Test getting GitHub repository."""
        mock_repo = Mock()
        mock_clone.return_value = mock_repo
        
        with patch('pathlib.Path') as mock_path:
            mock_path.cwd.return_value = Path('/current')
            mock_path.return_value.mkdir.return_value = None
            
            analyzer = RepoAnalyzer('https://github.com/username/repo')
            repo = analyzer._get_repo()
            
            assert repo == mock_repo
            mock_clone.assert_called_once()
    
    @patch('repo_analyzer.analyzer.RepoAnalyzer._analyze_files')
    @patch('repo_analyzer.analyzer.RepoAnalyzer._analyze_git_stats')
    @patch('repo_analyzer.analyzer.RepoAnalyzer._get_github_metadata')
    def test_analyze(self, mock_github_meta, mock_git_stats, mock_files):
        """Test complete analysis process."""
        # Mock return values
        mock_files.return_value = [
            FileInfo(
                path='test.py',
                size_bytes=1000,
                lines_of_code=50,
                lines_of_comments=10,
                blank_lines=5,
                language='Python',
                is_binary=False
            )
        ]
        
        mock_git_stats.return_value = GitStats(
            total_commits=10,
            contributors=['user1', 'user2'],
            top_contributors={'user1': 6, 'user2': 4},
            most_changed_files=['test.py'],
            commit_activity={'2023-01-01': 2}
        )
        
        mock_github_meta.return_value = None
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.working_dir = '/test/path'
        
        with patch('repo_analyzer.analyzer.RepoAnalyzer._get_repo', return_value=mock_repo):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.abspath', return_value='/test/path'):
                    analyzer = RepoAnalyzer('/test/path')
                    result = analyzer.analyze()
                    
                    assert isinstance(result, AnalysisResult)
                    assert result.total_files == 1
                    assert result.total_lines_of_code == 50
                    assert result.total_lines_of_comments == 10
                    assert result.total_blank_lines == 5
                    assert len(result.languages) == 1
                    assert result.languages[0].language == 'Python'
                    assert result.git_stats.total_commits == 10
    
    def test_should_skip_file(self):
        """Test file skipping logic."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.abspath', return_value='/test/path'):
                analyzer = RepoAnalyzer('/test/path')
                
                # Should skip
                assert analyzer._should_skip_file(Path('.git/config')) is True
                assert analyzer._should_skip_file(Path('__pycache__/file.pyc')) is True
                assert analyzer._should_skip_file(Path('node_modules/file.js')) is True
                assert analyzer._should_skip_file(Path('file.pyc')) is True
                
                # Should not skip
                assert analyzer._should_skip_file(Path('src/main.py')) is False
                assert analyzer._should_skip_file(Path('README.md')) is False
    
    @patch('repo_analyzer.analyzer.is_binary_file')
    @patch('repo_analyzer.analyzer.count_lines')
    def test_analyze_single_file(self, mock_count_lines, mock_is_binary):
        """Test single file analysis."""
        mock_is_binary.return_value = False
        mock_count_lines.return_value = (50, 10, 5)
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.abspath', return_value='/test/path'):
                analyzer = RepoAnalyzer('/test/path')
                
                # Mock file stats
                mock_file = Mock()
                mock_file.stat.return_value.st_size = 1000
                mock_file.relative_to.return_value = 'test.py'
                
                with patch('pathlib.Path') as mock_path:
                    mock_path.return_value = mock_file
                    
                    result = analyzer._analyze_single_file(
                        Path('test.py'), 
                        Path('/test/path')
                    )
                    
                    assert result is not None
                    assert result.path == 'test.py'
                    assert result.size_bytes == 1000
                    assert result.lines_of_code == 50
                    assert result.lines_of_comments == 10
                    assert result.blank_lines == 5
                    assert result.language == 'Python'
                    assert result.is_binary is False
    
    def test_detect_language(self):
        """Test language detection."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.abspath', return_value='/test/path'):
                analyzer = RepoAnalyzer('/test/path')
                
                # Test with known extensions
                assert analyzer._detect_language(Path('file.py')) == 'Python'
                assert analyzer._detect_language(Path('file.js')) == 'JavaScript'
                assert analyzer._detect_language(Path('file.java')) == 'Java'
                assert analyzer._detect_language(Path('file.cpp')) == 'C++'
                assert analyzer._detect_language(Path('file.md')) == 'Markdown'
                
                # Test with unknown extension
                assert analyzer._detect_language(Path('file.xyz')) == 'Unknown'
    
    def test_calculate_language_stats(self):
        """Test language statistics calculation."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.abspath', return_value='/test/path'):
                analyzer = RepoAnalyzer('/test/path')
                
                files_info = [
                    FileInfo(
                        path='file1.py',
                        size_bytes=1000,
                        lines_of_code=100,
                        lines_of_comments=20,
                        blank_lines=10,
                        language='Python',
                        is_binary=False
                    ),
                    FileInfo(
                        path='file2.py',
                        size_bytes=2000,
                        lines_of_code=200,
                        lines_of_comments=40,
                        blank_lines=20,
                        language='Python',
                        is_binary=False
                    ),
                    FileInfo(
                        path='file.js',
                        size_bytes=1500,
                        lines_of_code=150,
                        lines_of_comments=30,
                        blank_lines=15,
                        language='JavaScript',
                        is_binary=False
                    )
                ]
                
                total_lines = 450  # 100 + 200 + 150
                
                languages = analyzer._calculate_language_stats(files_info, total_lines)
                
                assert len(languages) == 2
                
                # Python should be first (more lines)
                assert languages[0].language == 'Python'
                assert languages[0].file_count == 2
                assert languages[0].total_lines == 300
                assert languages[0].percentage == pytest.approx(66.67, abs=0.01)
                
                # JavaScript should be second
                assert languages[1].language == 'JavaScript'
                assert languages[1].file_count == 1
                assert languages[1].total_lines == 150
                assert languages[1].percentage == pytest.approx(33.33, abs=0.01)
    
    def test_analyze_directory_structure(self):
        """Test directory structure analysis."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.abspath', return_value='/test/path'):
                analyzer = RepoAnalyzer('/test/path')
                
                files_info = [
                    FileInfo(
                        path='src/main.py',
                        size_bytes=1000,
                        lines_of_code=100,
                        lines_of_comments=20,
                        blank_lines=10,
                        language='Python',
                        is_binary=False
                    ),
                    FileInfo(
                        path='src/utils.py',
                        size_bytes=800,
                        lines_of_code=80,
                        lines_of_comments=16,
                        blank_lines=8,
                        language='Python',
                        is_binary=False
                    ),
                    FileInfo(
                        path='tests/test_main.py',
                        size_bytes=600,
                        lines_of_code=60,
                        lines_of_comments=12,
                        blank_lines=6,
                        language='Python',
                        is_binary=False
                    )
                ]
                
                structure = analyzer._analyze_directory_structure(files_info)
                
                assert structure['src'] == 2
                assert structure['tests'] == 1
    
    def test_cleanup(self):
        """Test cleanup method."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.abspath', return_value='/test/path'):
                analyzer = RepoAnalyzer('/test/path')
                
                # Test cleanup when no temporary repo
                analyzer.cleanup()  # Should not raise any errors
                
                # Test cleanup with temporary repo
                analyzer.is_github_repo = True
                mock_repo = Mock()
                mock_repo.working_dir = '/temp/repo'
                analyzer._repo = mock_repo
                
                with patch('shutil.rmtree') as mock_rmtree:
                    analyzer.cleanup()
                    mock_rmtree.assert_called_once_with('/temp/repo')


if __name__ == '__main__':
    pytest.main([__file__])
