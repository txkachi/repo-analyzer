"""GitHub API client for fetching repository metadata."""

import logging
from typing import Optional
from datetime import datetime

import requests

from .models import GitHubMetadata

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with the GitHub REST API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            })
        else:
            # Rate limit is much lower without authentication
            logger.warning("No GitHub token provided. API rate limits will be very restrictive.")
    
    def get_repo_metadata(self, owner: str, repo: str) -> Optional[GitHubMetadata]:
        """Get metadata for a GitHub repository.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            
        Returns:
            GitHubMetadata object or None if failed
        """
        try:
            # Get repository information
            repo_data = self._make_request(f"/repos/{owner}/{repo}")
            if not repo_data:
                return None
            
            # Get open issues count
            issues_data = self._make_request(f"/repos/{owner}/{repo}/issues?state=open&per_page=1")
            open_issues = issues_data.get("total_count", 0) if issues_data else 0
            
            # Get open pull requests count
            prs_data = self._make_request(f"/repos/{owner}/{repo}/pulls?state=open&per_page=1")
            open_pull_requests = prs_data.get("total_count", 0) if prs_data else 0
            
            # Parse dates
            created_at = None
            updated_at = None
            
            if repo_data.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            if repo_data.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            return GitHubMetadata(
                stars=repo_data.get("stargazers_count", 0),
                forks=repo_data.get("forks_count", 0),
                watchers=repo_data.get("watchers_count", 0),
                open_issues=open_issues,
                open_pull_requests=open_pull_requests,
                description=repo_data.get("description"),
                language=repo_data.get("language"),
                created_at=created_at,
                updated_at=updated_at,
            )
            
        except Exception as e:
            logger.error(f"Error fetching GitHub metadata for {owner}/{repo}: {e}")
            return None
    
    def _make_request(self, endpoint: str) -> Optional[dict]:
        """Make a request to the GitHub API.
        
        Args:
            endpoint: API endpoint (without base URL)
            
        Returns:
            Response data as dict or None if failed
        """
        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Repository not found: {endpoint}")
                return None
            elif response.status_code == 403:
                logger.warning(f"Access forbidden: {endpoint}. Check your token permissions.")
                return None
            elif response.status_code == 401:
                logger.warning(f"Unauthorized: {endpoint}. Check your token.")
                return None
            else:
                logger.warning(f"GitHub API error {response.status_code}: {endpoint}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}")
            return None
    
    def check_rate_limit(self) -> Optional[dict]:
        """Check the current rate limit status.
        
        Returns:
            Rate limit information or None if failed
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/rate_limit")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return None
    
    def close(self):
        """Close the session."""
        self.session.close()
